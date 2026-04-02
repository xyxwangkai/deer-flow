#!/usr/bin/env python3
"""
横向对比分析脚本：比较同一图表内不同曲线相对于 LOESS 预测的表现。

主要功能：
1. 对每条曲线计算 LOESS 预测残差的统计指标
2. 横向比较同一图表内不同曲线的表现
3. 识别相对于其他曲线表现异常的曲线（如震荡更剧烈、偏差更大等）

输出：
- 每个图表内曲线的对比排名
- 异常曲线的告警（相对于同图表其他曲线）
"""

import argparse
import json
import csv
import sys
import warnings
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from multiprocessing import Pool, cpu_count
from functools import partial

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.fft import fft
from scipy.stats import pearsonr

try:
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    LocalOutlierFactor = None
    IsolationForest = None


def setup_chinese_font():
    """设置中文字体"""
    chinese_fonts = [
        'Noto Sans CJK SC',
        'WenQuanYi Micro Hei',
        'Source Han Sans CN',
        'Arial Unicode MS',
        'SimHei',
        'PingFang SC',
        'Microsoft YaHei',
    ]
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
            break
    else:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False


setup_chinese_font()
warnings.filterwarnings('ignore')


@dataclass
class CrossCurveFeatures:
    """横向对比的多维特征"""
    robust_volatility_mad: float = 0.0
    relative_deviation_rate: float = 0.0
    hf_energy_ratio: float = 0.0
    consecutive_hit_rate: float = 0.0
    sample_size: int = 0
    z_score_max: float = 0.0
    pearson_corr_with_peer: float = 0.0
    tail_deviation: float = 0.0
    second_diff_volatility: float = 0.0
    lof_score: float = 0.0


@dataclass
class CurveMetrics:
    """单条曲线的统计指标"""
    legend: str
    insight_sid: str
    n_history: int
    n_new: int
    
    mean_residual: float
    std_residual: float
    max_abs_residual: float
    
    volatility: float
    direction_changes: int
    direction_change_ratio: float
    
    trend_slope: float
    
    anomaly_score: float
    
    peer_group: List[str] = field(default_factory=list)
    avg_peer_corr: float = 0.0


@dataclass
class CrossCurveAlert:
    """横向对比告警"""
    insight_sid: str
    insight_name: str
    legend: str
    alert_type: str
    score: float
    percentile: float
    message: str
    comparison: Dict[str, Any]
    features: Optional[CrossCurveFeatures] = None
    local_suggestion: str = "normal"


class CrossCurveAnalyzer:
    """横向对比分析器"""
    
    def __init__(
        self,
        smoothing_factor: float = 0.3,
        volatility_percentile: float = 90,
        peer_method: str = 'pearson',
        peer_threshold: float = 0.8,
        min_peer_size: int = 3,
        min_new_points: int = 2,
        enable_local_suggestion: bool = True,
        detection_method: str = 'lof',
        lof_contamination: float = 0.1,
        lof_n_neighbors: int = 3
    ):
        self.smoothing_factor = smoothing_factor
        self.volatility_percentile = volatility_percentile
        self.peer_method = peer_method
        self.peer_threshold = peer_threshold
        self.min_peer_size = min_peer_size
        self.min_new_points = min_new_points
        self.enable_local_suggestion = enable_local_suggestion
        self.detection_method = detection_method
        self.lof_contamination = lof_contamination
        self.lof_n_neighbors = lof_n_neighbors
    
    def _compute_peer_similarity(
        self,
        y1: np.ndarray,
        y2: np.ndarray
    ) -> float:
        """计算两条曲线的相似度"""
        if len(y1) < 3 or len(y2) < 3:
            return 0.0
        
        min_len = min(len(y1), len(y2))
        y1_aligned = y1[-min_len:]
        y2_aligned = y2[-min_len:]
        
        if self.peer_method == 'pearson':
            try:
                corr, _ = pearsonr(y1_aligned, y2_aligned)
                return float(corr) if not np.isnan(corr) else 0.0
            except Exception:
                return 0.0
        else:
            try:
                corr, _ = pearsonr(y1_aligned, y2_aligned)
                return float(corr) if not np.isnan(corr) else 0.0
            except Exception:
                return 0.0
    
    def _select_peer_group(
        self,
        target_legend: str,
        all_curves: Dict[str, np.ndarray]
    ) -> Tuple[List[str], float]:
        """
        为目标曲线选择 Peer Group
        
        Returns:
            (peer_legends, avg_correlation)
        """
        if target_legend not in all_curves:
            return [], 0.0
        
        target_y = all_curves[target_legend]
        similarities = []
        
        for legend, y in all_curves.items():
            if legend == target_legend:
                continue
            sim = self._compute_peer_similarity(target_y, y)
            similarities.append((legend, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        peer_group = [
            legend for legend, sim in similarities 
            if sim >= self.peer_threshold
        ]
        
        if len(peer_group) < self.min_peer_size:
            peer_group = [legend for legend, _ in similarities[:self.min_peer_size]]
        
        if peer_group:
            avg_corr = np.mean([
                sim for legend, sim in similarities 
                if legend in peer_group
            ])
        else:
            avg_corr = 0.0
        
        return peer_group, float(avg_corr)
    
    def _compute_hf_energy_ratio(self, y: np.ndarray) -> float:
        """计算高频能量比"""
        n = len(y)
        if n < 4:
            return 0.0
        
        try:
            y_centered = y - np.mean(y)
            fft_result = fft(y_centered)
            power_spectrum = np.abs(fft_result[:n//2])**2
            
            total_energy = np.sum(power_spectrum)
            if total_energy < 1e-10:
                return 0.0
            
            hf_start = n // 4
            hf_energy = np.sum(power_spectrum[hf_start:])
            
            return float(hf_energy / total_energy)
        except Exception:
            return 0.0
    
    def _compute_robust_volatility(self, residuals: np.ndarray) -> float:
        """计算鲁棒波动率"""
        if len(residuals) == 0:
            return 0.0
        mad = np.median(np.abs(residuals - np.median(residuals)))
        return float(1.4826 * mad)
    
    def _compute_tail_deviation(self, y_new: np.ndarray, residuals: np.ndarray, n_tail: int = 3) -> float:
        """计算尾部偏离度 - 最后 N 个点的平均偏离程度"""
        if len(residuals) < n_tail:
            n_tail = len(residuals)
        if n_tail == 0:
            return 0.0
        tail_residuals = residuals[-n_tail:]
        mean_y = np.mean(y_new) if len(y_new) > 0 else 1.0
        return float(np.mean(np.abs(tail_residuals)) / (abs(mean_y) + 1e-10))
    
    def _compute_second_diff_volatility(self, y_new: np.ndarray) -> float:
        """计算二阶差分波动 - 更好捕捉曲线的"颠簸"程度"""
        if len(y_new) < 3:
            return 0.0
        first_diff = np.diff(y_new)
        second_diff = np.diff(first_diff)
        return float(np.std(second_diff)) if len(second_diff) > 0 else 0.0
    
    def _detect_outliers_lof(
        self,
        feature_matrix: np.ndarray,
        n_neighbors: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用 Local Outlier Factor 检测离群曲线
        
        Args:
            feature_matrix: 特征矩阵 (n_samples, n_features)
            n_neighbors: 邻居数量
        
        Returns:
            (labels, scores): 标签 (-1 为离群), LOF 分数
        """
        n_samples = len(feature_matrix)
        if n_samples < 3:
            return np.ones(n_samples), np.zeros(n_samples)
        
        if n_neighbors is None:
            n_neighbors = min(self.lof_n_neighbors, n_samples - 1)
        else:
            n_neighbors = min(n_neighbors, n_samples - 1)
        
        X = feature_matrix.copy()
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0)
        X_std[X_std < 1e-10] = 1.0
        X_normalized = (X - X_mean) / X_std
        
        try:
            lof = LocalOutlierFactor(
                n_neighbors=n_neighbors,
                contamination=self.lof_contamination,
                novelty=False
            )
            labels = lof.fit_predict(X_normalized)
            scores = -lof.negative_outlier_factor_
        except Exception:
            labels = np.ones(n_samples)
            scores = np.zeros(n_samples)
        
        return labels, scores
    
    def _detect_outliers_iforest(
        self,
        feature_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用 Isolation Forest 检测离群曲线
        
        Returns:
            (labels, scores): 标签 (-1 为离群), 异常分数
        """
        n_samples = len(feature_matrix)
        if n_samples < 3:
            return np.ones(n_samples), np.zeros(n_samples)
        
        X = feature_matrix.copy()
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0)
        X_std[X_std < 1e-10] = 1.0
        X_normalized = (X - X_mean) / X_std
        
        try:
            iforest = IsolationForest(
                contamination=self.lof_contamination,
                random_state=42,
                n_estimators=100
            )
            labels = iforest.fit_predict(X_normalized)
            scores = -iforest.decision_function(X_normalized)
        except Exception:
            labels = np.ones(n_samples)
            scores = np.zeros(n_samples)
        
        return labels, scores
    
    def _compute_local_suggestion(self, features: CrossCurveFeatures) -> str:
        """计算局部判据建议
        
        核心逻辑：真正的"震荡"应该体现在方向频繁变化或高频能量比高。
        平滑下降的曲线不应该被标记为异常。
        """
        if not self.enable_local_suggestion:
            return "normal"
        
        if features.consecutive_hit_rate < 0.2:
            return "normal"
        
        high_confidence_count = 0
        
        if features.hf_energy_ratio > 0.7:
            high_confidence_count += 1
        if features.consecutive_hit_rate > 0.5:
            high_confidence_count += 1
        if features.robust_volatility_mad > 0.02:
            high_confidence_count += 1
        
        if high_confidence_count >= 2 and features.consecutive_hit_rate > 0.3:
            return "high_confidence_anomaly"
        elif high_confidence_count >= 1:
            return "potential_fluctuation"
        else:
            return "normal"
    
    def _predict_loess(
        self,
        x_history: np.ndarray,
        y_history: np.ndarray,
        x_new: float
    ) -> float:
        """LOESS 预测（优化版本）"""
        n = len(x_history)
        if n == 0:
            return 0.0
        
        bandwidth = self.smoothing_factor * (x_history.max() - x_history.min() + 1e-6)
        weights = np.exp(-0.5 * ((x_history - x_new) / bandwidth) ** 2)
        weights_sum = weights.sum()
        
        if weights_sum < 1e-10:
            return y_history[-1]
        
        weights = weights / weights_sum
        y_pred = np.dot(weights, y_history)
        
        if n >= 3:
            x_mean = np.dot(weights, x_history)
            x_centered = x_history - x_mean
            y_centered = y_history - y_pred
            
            wxx = np.dot(weights * x_centered, x_centered)
            
            if wxx > 1e-10:
                wxy = np.dot(weights * x_centered, y_centered)
                slope = wxy / wxx
                y_pred = y_pred + slope * (x_new - x_mean)
        
        return y_pred
    
    def _compute_curve_metrics(
        self,
        legend: str,
        df_curve: pd.DataFrame,
        insight_sid: str,
        all_history_curves: Optional[Dict[str, np.ndarray]] = None
    ) -> Optional[CurveMetrics]:
        """计算单条曲线的统计指标"""
        df_curve = df_curve.sort_values('x').reset_index(drop=True)
        
        history_df = df_curve[df_curve['is_new'] == 0]
        new_df = df_curve[df_curve['is_new'] == 1]
        
        if len(history_df) < 3 or len(new_df) < self.min_new_points:
            return None
        
        x_history = history_df['x'].values
        y_history = history_df['y'].values
        x_new = new_df['x'].values
        y_new = new_df['y'].values
        
        y_preds = np.array([self._predict_loess(x_history, y_history, x) for x in x_new])
        residuals = y_new - y_preds
        
        mean_residual = np.mean(residuals)
        std_residual = np.std(residuals)
        max_abs_residual = np.max(np.abs(residuals))
        
        volatility = np.std(residuals) if len(residuals) > 0 else np.std(y_new)
        
        diffs = np.diff(y_new)
        direction_changes = 0
        for i in range(1, len(diffs)):
            if diffs[i] * diffs[i-1] < 0:
                direction_changes += 1
        
        max_changes = len(y_new) - 2
        direction_change_ratio = direction_changes / max_changes if max_changes > 0 else 0
        
        if len(y_new) >= 2:
            trend_slope = (y_new[-1] - y_new[0]) / (x_new[-1] - x_new[0] + 1e-10)
        else:
            trend_slope = 0.0
        
        anomaly_score = (
            abs(mean_residual) * 10 +
            std_residual * 5 +
            volatility * 3 +
            direction_change_ratio * 2
        )
        
        peer_group = []
        avg_peer_corr = 0.0
        if all_history_curves:
            peer_group, avg_peer_corr = self._select_peer_group(legend, all_history_curves)
        
        return CurveMetrics(
            legend=legend,
            insight_sid=insight_sid,
            n_history=len(history_df),
            n_new=len(new_df),
            mean_residual=mean_residual,
            std_residual=std_residual,
            max_abs_residual=max_abs_residual,
            volatility=volatility,
            direction_changes=direction_changes,
            direction_change_ratio=direction_change_ratio,
            trend_slope=trend_slope,
            anomaly_score=anomaly_score,
            peer_group=peer_group,
            avg_peer_corr=avg_peer_corr
        )
    
    def analyze_insight(
        self,
        df_insight: pd.DataFrame,
        insight_sid: str,
        insight_name: str
    ) -> Tuple[List[CurveMetrics], List[CrossCurveAlert]]:
        """分析单个图表内的所有曲线"""
        all_history_curves: Dict[str, np.ndarray] = {}
        for legend in df_insight['legend'].unique():
            df_curve = df_insight[df_insight['legend'] == legend].copy()
            history_df = df_curve[df_curve['is_new'] == 0].sort_values('x')
            if len(history_df) >= 3:
                all_history_curves[legend] = history_df['y'].values
        
        metrics_list = []
        curve_new_data: Dict[str, np.ndarray] = {}
        curve_residuals: Dict[str, np.ndarray] = {}
        curve_data_cache: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
        
        for legend in df_insight['legend'].unique():
            df_curve = df_insight[df_insight['legend'] == legend].copy()
            
            history_df = df_curve[df_curve['is_new'] == 0].sort_values('x')
            new_df = df_curve[df_curve['is_new'] == 1].sort_values('x')
            
            if len(history_df) >= 3 and len(new_df) >= self.min_new_points:
                x_history = history_df['x'].values
                y_history = history_df['y'].values
                x_new = new_df['x'].values
                y_new = new_df['y'].values
                curve_data_cache[legend] = (x_history, y_history, x_new, y_new)
            
            metrics = self._compute_curve_metrics(
                legend, df_curve, insight_sid, all_history_curves
            )
            if metrics:
                metrics_list.append(metrics)
                curve_new_data[legend] = new_df['y'].values
                
                if legend in curve_data_cache:
                    x_history, y_history, x_new, y_new = curve_data_cache[legend]
                    y_preds = np.array([self._predict_loess(x_history, y_history, x) for x in x_new])
                    curve_residuals[legend] = y_new - y_preds
        
        if len(metrics_list) < 2:
            return metrics_list, []
        
        alerts = []
        
        features_list: List[CrossCurveFeatures] = []
        for metrics in metrics_list:
            y_new = curve_new_data.get(metrics.legend, np.array([]))
            residuals = curve_residuals.get(metrics.legend, np.array([]))
            
            features = CrossCurveFeatures(
                robust_volatility_mad=self._compute_robust_volatility(residuals) if len(residuals) > 0 else 0.0,
                relative_deviation_rate=metrics.max_abs_residual / (abs(np.mean(y_new)) + 1e-10) if len(y_new) > 0 else 0.0,
                hf_energy_ratio=self._compute_hf_energy_ratio(y_new) if len(y_new) > 0 else 0.0,
                consecutive_hit_rate=metrics.direction_change_ratio,
                sample_size=metrics.n_new,
                z_score_max=0.0,
                pearson_corr_with_peer=metrics.avg_peer_corr,
                tail_deviation=self._compute_tail_deviation(y_new, residuals) if len(residuals) > 0 else 0.0,
                second_diff_volatility=self._compute_second_diff_volatility(y_new) if len(y_new) > 0 else 0.0,
                lof_score=0.0
            )
            features_list.append(features)
        
        use_sklearn_detection = (
            self.detection_method in ('lof', 'iforest') 
            and len(metrics_list) >= 3 
            and SKLEARN_AVAILABLE
        )
        
        if use_sklearn_detection:
            feature_matrix = np.array([
                [
                    f.robust_volatility_mad,
                    f.hf_energy_ratio,
                    f.consecutive_hit_rate,
                    f.second_diff_volatility,
                    f.tail_deviation,
                    m.trend_slope
                ]
                for m, f in zip(metrics_list, features_list)
            ])
            
            if self.detection_method == 'lof':
                labels, scores = self._detect_outliers_lof(feature_matrix)
            else:
                labels, scores = self._detect_outliers_iforest(feature_matrix)
            
            for i, (metrics, features) in enumerate(zip(metrics_list, features_list)):
                features.lof_score = float(scores[i])
                
                if labels[i] == -1:
                    local_suggestion = self._compute_local_suggestion(features)
                    
                    if local_suggestion in ("high_confidence_anomaly", "potential_fluctuation"):
                        outlier_features = []
                        feature_names = ['robust_volatility_mad', 'hf_energy_ratio', 'consecutive_hit_rate',
                                        'second_diff_volatility', 'tail_deviation', 'trend_slope']
                        feature_values = feature_matrix[i]
                        feature_means = feature_matrix.mean(axis=0)
                        feature_stds = feature_matrix.std(axis=0)
                        
                        for j, fname in enumerate(feature_names):
                            if feature_stds[j] > 1e-10:
                                z = (feature_values[j] - feature_means[j]) / feature_stds[j]
                                if abs(z) > 2.0:
                                    outlier_features.append(f"{fname}(z={z:.1f})")
                        
                        alerts.append(CrossCurveAlert(
                            insight_sid=insight_sid,
                            insight_name=insight_name,
                            legend=metrics.legend,
                            alert_type="outlier",
                            score=float(scores[i]),
                            percentile=float((np.sum(scores <= scores[i]) / len(scores)) * 100),
                            message=f"曲线形态与同图表其他曲线显著不同 (LOF={scores[i]:.2f}, 异常特征: {', '.join(outlier_features) if outlier_features else '综合'})",
                            comparison={
                                "lof_score": float(scores[i]),
                                "outlier_features": outlier_features,
                                "detection_method": self.detection_method,
                                "n_curves": len(metrics_list)
                            },
                            features=features,
                            local_suggestion=local_suggestion
                        ))
        else:
            volatilities = [m.volatility for m in metrics_list]
            vol_mean = np.mean(volatilities)
            vol_std = np.std(volatilities)
            vol_threshold = np.percentile(volatilities, self.volatility_percentile)
            
            change_ratios = [m.direction_change_ratio for m in metrics_list]
            change_threshold = np.percentile(change_ratios, self.volatility_percentile)
            
            for i, (metrics, features) in enumerate(zip(metrics_list, features_list)):
                vol_percentile = (np.sum(np.array(volatilities) <= metrics.volatility) / len(volatilities)) * 100
                change_percentile = (np.sum(np.array(change_ratios) <= metrics.direction_change_ratio) / len(change_ratios)) * 100
                
                peer_volatilities = [
                    m.volatility for m in metrics_list 
                    if m.legend in metrics.peer_group
                ] if metrics.peer_group else volatilities
                
                peer_vol_mean = np.mean(peer_volatilities) if peer_volatilities else vol_mean
                peer_vol_std = np.std(peer_volatilities) if peer_volatilities else vol_std
                if peer_vol_std < 1e-10:
                    peer_vol_std = vol_std if vol_std > 1e-10 else peer_vol_mean * 0.1 if peer_vol_mean > 0 else 1e-6
                
                features.z_score_max = (metrics.volatility - peer_vol_mean) / (peer_vol_std + 1e-10)
                
                min_abs_volatility = 0.005
                if metrics.volatility > vol_threshold and vol_std > 1e-10 and metrics.volatility > min_abs_volatility:
                    vol_zscore = (metrics.volatility - peer_vol_mean) / (peer_vol_std + 1e-10)
                    if vol_zscore > 3.0:
                        local_suggestion = self._compute_local_suggestion(features)
                        if local_suggestion == "high_confidence_anomaly":
                            alerts.append(CrossCurveAlert(
                                insight_sid=insight_sid,
                                insight_name=insight_name,
                                legend=metrics.legend,
                                alert_type="high_volatility",
                                score=vol_zscore,
                                percentile=vol_percentile,
                                message=f"波动率显著高于同图表其他曲线 (z={vol_zscore:.2f}, 百分位={vol_percentile:.0f}%)",
                                comparison={
                                    "this_curve": metrics.volatility,
                                    "mean": peer_vol_mean,
                                    "std": peer_vol_std,
                                    "threshold": vol_threshold,
                                    "peer_count": len(metrics.peer_group)
                                },
                                features=features,
                                local_suggestion=local_suggestion
                            ))
                
                min_direction_change_ratio = 0.3
                if metrics.direction_change_ratio > change_threshold and len(change_ratios) > 2 and metrics.direction_change_ratio > min_direction_change_ratio:
                    change_mean = np.mean(change_ratios)
                    change_std = np.std(change_ratios)
                    if change_std > 1e-10:
                        change_zscore = (metrics.direction_change_ratio - change_mean) / change_std
                        if change_zscore > 3.0:
                            local_suggestion = self._compute_local_suggestion(features)
                            if local_suggestion == "high_confidence_anomaly":
                                alerts.append(CrossCurveAlert(
                                    insight_sid=insight_sid,
                                    insight_name=insight_name,
                                    legend=metrics.legend,
                                    alert_type="unstable",
                                    score=change_zscore,
                                    percentile=change_percentile,
                                    message=f"方向变化频率显著高于同图表其他曲线 (z={change_zscore:.2f}, 百分位={change_percentile:.0f}%)",
                                    comparison={
                                        "this_curve": metrics.direction_change_ratio,
                                        "direction_changes": metrics.direction_changes,
                                        "mean": change_mean,
                                        "std": change_std
                                    },
                                    features=features,
                                    local_suggestion=local_suggestion
                                ))
        
        return metrics_list, alerts
    
    def analyze(
        self,
        df: pd.DataFrame,
        legend_col: str = 'legend',
        x_col: str = 'x',
        y_col: str = 'y',
        is_new_col: str = 'is_new',
        insight_sid_col: str = 'insight_sid',
        insight_name_col: str = 'insight_name',
        n_jobs: int = 1
    ) -> Tuple[Dict[str, List[CurveMetrics]], List[CrossCurveAlert]]:
        """分析整个数据集"""
        df = df.rename(columns={
            x_col: 'x',
            y_col: 'y',
            is_new_col: 'is_new',
            legend_col: 'legend'
        })
        
        insight_sids = df[insight_sid_col].unique()
        
        min_insights_for_parallel = 10
        
        if n_jobs == 1 or len(insight_sids) < min_insights_for_parallel:
            all_metrics = {}
            all_alerts = []
            
            for insight_sid in insight_sids:
                df_insight = df[df[insight_sid_col] == insight_sid].copy()
                
                if insight_name_col in df.columns:
                    insight_name = df_insight[insight_name_col].iloc[0]
                else:
                    insight_name = insight_sid
                
                metrics_list, alerts = self.analyze_insight(df_insight, insight_sid, insight_name)
                
                if metrics_list:
                    all_metrics[insight_sid] = metrics_list
                
                all_alerts.extend(alerts)
        else:
            if n_jobs == -1:
                n_jobs = min(cpu_count(), 8)
            
            insight_data = []
            for insight_sid in insight_sids:
                df_insight = df[df[insight_sid_col] == insight_sid].copy()
                
                if insight_name_col in df.columns:
                    insight_name = df_insight[insight_name_col].iloc[0]
                else:
                    insight_name = insight_sid
                
                insight_data.append((df_insight, insight_sid, insight_name))
            
            analyze_func = partial(self._analyze_insight_wrapper)
            
            with Pool(processes=n_jobs) as pool:
                results = pool.map(analyze_func, insight_data)
            
            all_metrics = {}
            all_alerts = []
            for metrics_list, alerts in results:
                if metrics_list:
                    all_metrics[metrics_list[0].insight_sid if metrics_list else None] = metrics_list
                all_alerts.extend(alerts)
        
        all_alerts.sort(key=lambda x: x.score, reverse=True)
        
        return all_metrics, all_alerts
    
    def _analyze_insight_wrapper(self, args: Tuple[pd.DataFrame, str, str]) -> Tuple[List[CurveMetrics], List[CrossCurveAlert]]:
        """多进程包装函数"""
        df_insight, insight_sid, insight_name = args
        return self.analyze_insight(df_insight, insight_sid, insight_name)
    
    def plot_comparison(
        self,
        df: pd.DataFrame,
        insight_sid: str,
        output_path: str,
        highlight_legends: Optional[List[str]] = None,
        n_reference_curves: int = 3
    ):
        """
        绘制同一图表内曲线的对比图
        
        只显示有问题的曲线和少量正常曲线作为参照
        
        Args:
            df: 数据
            insight_sid: 图表 ID
            output_path: 输出路径
            highlight_legends: 需要高亮的曲线（有问题的曲线）
            n_reference_curves: 参照曲线数量（正常曲线）
        """
        df_insight = df[df['insight_sid'] == insight_sid].copy()
        
        if 'insight_name' in df.columns:
            insight_name = df_insight['insight_name'].iloc[0]
        else:
            insight_name = insight_sid
        
        all_legends = df_insight['legend'].unique().tolist()
        
        if len(all_legends) == 0:
            return
        
        highlight_set = set(highlight_legends) if highlight_legends else set()
        normal_legends = [l for l in all_legends if l not in highlight_set]
        
        curve_volatilities = []
        for legend in normal_legends:
            df_curve = df_insight[df_insight['legend'] == legend].sort_values('x')
            new_data = df_curve[df_curve['is_new'] == 1]['y'].values
            if len(new_data) >= 2:
                volatility = np.std(new_data)
                curve_volatilities.append((legend, volatility))
        
        curve_volatilities.sort(key=lambda x: x[1])
        
        if len(curve_volatilities) >= n_reference_curves:
            step = len(curve_volatilities) // n_reference_curves
            reference_legends = [curve_volatilities[i * step][0] for i in range(n_reference_curves)]
        else:
            reference_legends = [c[0] for c in curve_volatilities]
        
        legends_to_plot = list(highlight_set) + reference_legends
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for legend in reference_legends:
            df_curve = df_insight[df_insight['legend'] == legend].sort_values('x')
            short_legend = legend[:40] + '...' if len(legend) > 40 else legend
            ax.plot(df_curve['x'], df_curve['y'], 
                   color='gray', linewidth=1.0, alpha=0.5,
                   label=f'[参照] {short_legend}')
        
        highlight_colors = ['red', 'orange', 'purple', 'brown']
        for i, legend in enumerate(highlight_set):
            df_curve = df_insight[df_insight['legend'] == legend].sort_values('x')
            color = highlight_colors[i % len(highlight_colors)]
            short_legend = legend[:40] + '...' if len(legend) > 40 else legend
            ax.plot(df_curve['x'], df_curve['y'], 
                   color=color, linewidth=2.5, alpha=1.0,
                   label=f'[异常] {short_legend}', marker='o', markersize=5)
        
        ax.set_xlabel('X (训练步数)', fontsize=11)
        ax.set_ylabel('Y (指标值)', fontsize=11)
        
        title = f'横向对比: {insight_name[:60]}' if len(insight_name) <= 60 else f'横向对比: {insight_name[:60]}...'
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        info_text = f"显示曲线: {len(legends_to_plot)} / {len(all_legends)}\n异常曲线: {len(highlight_set)}\n参照曲线: {len(reference_legends)}"
        ax.text(0.98, 0.02, info_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()


def write_cross_alerts_csv(alerts: List[CrossCurveAlert], output_path: str) -> None:
    """将横向对比告警列表写入 CSV 文件"""
    fieldnames = [
        'legend', 'insight_sid', 'insight_name', 'type', 'score', 'percentile', 'message',
        'robust_volatility_mad', 'relative_deviation_rate', 'hf_energy_ratio',
        'consecutive_hit_rate', 'sample_size', 'z_score_max', 'pearson_corr_with_peer',
        'tail_deviation', 'second_diff_volatility', 'lof_score', 'local_suggestion'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for a in alerts:
            features = a.features if a.features else CrossCurveFeatures()
            row = {
                'legend': a.legend,
                'insight_sid': a.insight_sid,
                'insight_name': a.insight_name,
                'type': a.alert_type,
                'score': f"{a.score:.2f}",
                'percentile': f"{a.percentile:.1f}",
                'message': a.message,
                'robust_volatility_mad': f"{features.robust_volatility_mad:.4f}",
                'relative_deviation_rate': f"{features.relative_deviation_rate:.4f}",
                'hf_energy_ratio': f"{features.hf_energy_ratio:.4f}",
                'consecutive_hit_rate': f"{features.consecutive_hit_rate:.4f}",
                'sample_size': features.sample_size,
                'z_score_max': f"{features.z_score_max:.2f}",
                'pearson_corr_with_peer': f"{features.pearson_corr_with_peer:.4f}",
                'tail_deviation': f"{features.tail_deviation:.4f}",
                'second_diff_volatility': f"{features.second_diff_volatility:.6f}",
                'lof_score': f"{features.lof_score:.4f}",
                'local_suggestion': a.local_suggestion
            }
            writer.writerow(row)


def write_cross_summary_txt(
    input_file: str,
    total_insights: int,
    total_alerts: int,
    percentile_threshold: float,
    output_path: str
) -> None:
    """写入横向对比摘要文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"total_insights={total_insights},total_alerts={total_alerts},percentile_threshold={percentile_threshold:.1f}\n")


def main():
    start_time = time.time()
    
    parser = argparse.ArgumentParser(
        description='横向对比分析：比较同一图表内不同曲线的表现',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法
  python3 cross_curve_analysis.py case.csv
  
  # 输出到 CSV 文件（默认）
  python3 cross_curve_analysis.py case.csv -o comparison
  
  # 输出到 JSON 文件
  python3 cross_curve_analysis.py case.csv -o comparison -f json
  
  # 生成对比图
  python3 cross_curve_analysis.py case.csv -p ./comparison_plots/
  
  # 只分析指定的 insight
  python3 cross_curve_analysis.py case.csv -i alsj12j4wn689ed704
"""
    )
    
    parser.add_argument('input', help='输入 CSV 文件路径')
    parser.add_argument('-o', '--output', help='输出结果路径（不含扩展名）')
    parser.add_argument('-f', '--output-format', choices=['csv', 'json', 'both'],
                       default='csv', help='输出格式（默认: csv）')
    parser.add_argument('-p', '--plot-dir', help='输出对比图目录')
    parser.add_argument('-i', '--insight-sids', nargs='+', help='只分析指定的 insight_sid')
    parser.add_argument('-t', '--percentile-threshold', type=float, default=90,
                       help='百分位阈值，默认 90')
    parser.add_argument('--peer-method', choices=['pearson', 'dtw'], default='pearson',
                       help='Peer 选取方法（默认: pearson）')
    parser.add_argument('--peer-threshold', type=float, default=0.8,
                       help='Peer Group 筛选阈值（默认: 0.8）')
    parser.add_argument('--min-peer-size', type=int, default=3,
                       help='最小 Peer Group 规模（默认: 3）')
    parser.add_argument('--min-new-points', type=int, default=2,
                       help='最少新增数据点数量（默认: 2）')
    parser.add_argument('--no-local-suggestion', action='store_true',
                       help='关闭局部判据建议')
    parser.add_argument('--detection-method', choices=['lof', 'iforest', 'zscore'],
                       default='lof', help='检测方法: lof(LOF离群因子), iforest(孤立森林), zscore(z-score阈值)（默认: lof）')
    parser.add_argument('--lof-contamination', type=float, default=0.1,
                       help='LOF/IsolationForest 异常比例参数（默认: 0.1）')
    parser.add_argument('--lof-n-neighbors', type=int, default=3,
                       help='LOF 邻居数量（默认: 3）')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式')
    parser.add_argument('-j', '--jobs', type=int, default=1,
                       help='并行进程数，-1 表示使用所有 CPU 核心 (默认: 1, 单进程)')
    
    args = parser.parse_args()
    
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"错误: 文件不存在: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    if not args.quiet:
        print(f"[性能优化] 正在读取 CSV...")
    
    df = pd.read_csv(csv_path, dtype={'is_new': 'int8'})
    
    if args.insight_sids:
        df = df[df['insight_sid'].isin(args.insight_sids)]
    
    if not args.quiet:
        print(f"\n读取 CSV: {csv_path.absolute()}")
        print(f"总行数: {len(df)}")
        print(f"图表数: {df['insight_sid'].nunique()}")
        print(f"曲线数: {df['legend'].nunique()}")
        print(f"检测方法: {args.detection_method}")
        if args.jobs > 1 or args.jobs == -1:
            total_insights = df['insight_sid'].nunique()
            min_insights_for_parallel = 10
            if total_insights >= min_insights_for_parallel:
                actual_jobs = args.jobs if args.jobs > 0 else min(cpu_count(), 8)
                print(f"[性能优化] 使用多进程模式: {actual_jobs} 个进程 ({total_insights} 个图表)")
            else:
                print(f"[性能优化] 图表数量较少 ({total_insights} < {min_insights_for_parallel})，使用单进程模式")
    
    analyzer = CrossCurveAnalyzer(
        volatility_percentile=args.percentile_threshold,
        peer_method=args.peer_method,
        peer_threshold=args.peer_threshold,
        min_peer_size=args.min_peer_size,
        min_new_points=args.min_new_points,
        enable_local_suggestion=not args.no_local_suggestion,
        detection_method=args.detection_method,
        lof_contamination=args.lof_contamination,
        lof_n_neighbors=args.lof_n_neighbors
    )
    
    all_metrics, alerts = analyzer.analyze(df, n_jobs=args.jobs)
    
    if not args.quiet:
        print(f"\n=== 横向对比分析完成 ===")
        print(f"分析图表数: {len(all_metrics)}")
        print(f"检测到告警: {len(alerts)} 个")
        
        if alerts:
            print(f"\n告警详情 (按显著程度排序):")
            for i, alert in enumerate(alerts[:10], 1):
                print(f"  {i}. [{alert.alert_type}] {alert.legend[:50]}...")
                print(f"     图表: {alert.insight_name[:40]}...")
                print(f"     建议: {alert.local_suggestion}")
                print(f"     {alert.message}")
    
    if args.plot_dir:
        plot_dir = Path(args.plot_dir)
        plot_dir.mkdir(parents=True, exist_ok=True)
        
        alert_legends_by_insight = {}
        for alert in alerts:
            if alert.insight_sid not in alert_legends_by_insight:
                alert_legends_by_insight[alert.insight_sid] = []
            alert_legends_by_insight[alert.insight_sid].append(alert.legend)
        
        for insight_sid in all_metrics.keys():
            highlight = alert_legends_by_insight.get(insight_sid, None)
            
            if not highlight:
                continue
            
            safe_name = insight_sid.replace('/', '_').replace('\\', '_')[:30]
            output_path = plot_dir / f"comparison_{safe_name}.png"
            
            analyzer.plot_comparison(df, insight_sid, str(output_path), highlight)
            
            if not args.quiet:
                print(f"  -> 生成对比图: {output_path.name}")
    
    if args.output:
        base_path = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
        
        if args.output_format in ('csv', 'both'):
            csv_out = f"{base_path}.csv"
            summary_out = f"{base_path}_summary.txt"
            write_cross_alerts_csv(alerts, csv_out)
            write_cross_summary_txt(str(csv_path), len(all_metrics), len(alerts),
                                   args.percentile_threshold, summary_out)
            if not args.quiet:
                print(f"\n结果已保存到: {csv_out}")
                print(f"摘要已保存到: {summary_out}")
        
        if args.output_format in ('json', 'both'):
            json_out = f"{base_path}.json"
            output_data = {
                "input_file": str(csv_path),
                "total_insights": len(all_metrics),
                "total_alerts": len(alerts),
                "alerts": [asdict(a) for a in alerts],
                "metrics_by_insight": {
                    sid: [asdict(m) for m in metrics]
                    for sid, metrics in all_metrics.items()
                }
            }
            
            with open(json_out, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            if not args.quiet:
                print(f"\n已保存到: {json_out}")
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if not args.quiet:
        print(f"\n代码执行时间: {execution_time:.2f} 秒")
    else:
        print(f"代码执行时间: {execution_time:.2f} 秒")


if __name__ == '__main__':
    main()