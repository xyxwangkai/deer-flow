#!/usr/bin/env python3
"""
单次异常检测脚本：对单个 CSV 快照进行异常检测。

输入 CSV 需要包含以下列：
- legend: 曲线名称
- x: 数据点 x 坐标
- y: 数据点 y 坐标
- is_new: 是否为新增数据点 (0=旧数据/历史数据, 1=新数据)

输出：
- 告警图片（可选）
- JSON 格式的分析结果
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import warnings
from scipy import stats
from scipy.fft import fft
import argparse
from pathlib import Path
import json
import csv
import os
import time
from multiprocessing import Pool, cpu_count
from functools import partial

try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    prange = range
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def setup_chinese_font():
    """设置中文字体，兼容 macOS 和 Linux"""
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


@jit(nopython=True, cache=True)
def _compute_loess_weights(x_train, x_target, bandwidth_sq):
    """使用 Numba 加速的权重计算"""
    n = len(x_train)
    weights = np.empty(n)
    for i in range(n):
        dist_sq = (x_train[i] - x_target) ** 2
        weights[i] = np.exp(-0.5 * dist_sq / bandwidth_sq)
    return weights

@jit(nopython=True, cache=True)
def _predict_loess_numba(x_train, y_train, x_target, bandwidth_sq):
    """使用 Numba 加速的 LOESS 预测"""
    n = len(x_train)
    
    weights = _compute_loess_weights(x_train, x_target, bandwidth_sq)
    weights_sum = np.sum(weights)
    
    if weights_sum < 1e-10:
        return y_train[-1]
    
    weights = weights / weights_sum
    y_pred = np.dot(weights, y_train)
    
    if n >= 3:
        x_mean = np.dot(weights, x_train)
        
        wxx = 0.0
        wxy = 0.0
        for i in range(n):
            x_c = x_train[i] - x_mean
            y_c = y_train[i] - y_pred
            wxx += weights[i] * x_c * x_c
            wxy += weights[i] * x_c * y_c
        
        if wxx > 1e-10:
            slope = wxy / wxx
            y_pred = y_pred + slope * (x_target - x_mean)
    
    return y_pred

@jit(nopython=True, cache=True)
def _compute_median_absolute_deviation(residuals):
    """使用 Numba 加速的 MAD 计算"""
    median_residual = np.median(residuals)
    abs_deviations = np.abs(residuals - median_residual)
    mad = np.median(abs_deviations)
    return 1.4826 * mad if mad > 0 else 0.1


class AnomalyType(Enum):
    POINT = "point"
    STEP_DOWN = "step_down"
    STEP_UP = "step_up"
    TREND_CHANGE = "trend_change"


@dataclass
class AnomalyFeatures:
    robust_volatility_mad: float = 0.0
    relative_deviation_rate: float = 0.0
    hf_energy_ratio: float = 0.0
    consecutive_hit_rate: float = 0.0
    sample_size: int = 0
    z_score_max: float = 0.0
    pearson_corr_with_peer: float = 0.0


@dataclass
class AnomalyAlert:
    legend: str
    x_start: float
    x_end: float
    y_observed: float
    y_predicted: float
    z_score: float
    anomaly_type: AnomalyType
    confidence: float
    message: str
    insight_sid: Optional[str] = None
    features: Optional[AnomalyFeatures] = None
    local_suggestion: str = "normal"


class SingleSnapshotAnalyzer:
    """
    单次快照异常检测器
    
    基于 is_new 字段区分历史数据和新增数据：
    - 历史数据 (is_new=0): 用于训练 LOESS 模型
    - 新增数据 (is_new=1): 被检测的数据点
    """
    
    def __init__(
        self,
        z_threshold: float = 4.0,
        consecutive_threshold: int = 3,
        min_history: int = 3,
        smoothing_factor: float = 0.3,
        min_abs_deviation: float = 0.02,
        min_rel_deviation: float = 0.03,
        min_new_points: int = 2,
        enable_local_suggestion: bool = True
    ):
        self.z_threshold = z_threshold
        self.consecutive_threshold = consecutive_threshold
        self.min_history = min_history
        self.smoothing_factor = smoothing_factor
        self.min_abs_deviation = min_abs_deviation
        self.min_rel_deviation = min_rel_deviation
        self.min_new_points = min_new_points
        self.enable_local_suggestion = enable_local_suggestion
    
    def _compute_robust_volatility(self, residuals: np.ndarray) -> float:
        """
        计算鲁棒波动率 (MAD)
        使用中位数绝对偏差计算新增数据点序列相对其 LOESS 预测值的离散程度
        """
        if len(residuals) == 0:
            return 0.0
        mad = np.median(np.abs(residuals - np.median(residuals)))
        return float(1.4826 * mad)
    
    def _compute_relative_deviation(
        self, 
        max_abs_deviation: float, 
        history_mean: float
    ) -> float:
        """
        计算相对偏差率
        最大绝对偏差与历史均值的比率，衡量偏差的业务显著性
        """
        if abs(history_mean) < 1e-10:
            return 0.0
        return float(abs(max_abs_deviation) / abs(history_mean))
    
    def _compute_hf_energy_ratio(self, y_new: np.ndarray) -> float:
        """
        计算高频能量比
        对新增数据点序列进行 FFT，计算高频部分能量占比，用于判断"剧烈抖动"
        """
        n = len(y_new)
        if n < 4:
            return 0.0
        
        try:
            y_centered = y_new - np.mean(y_new)
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
    
    def _compute_consecutive_hit_rate(
        self, 
        z_scores: np.ndarray, 
        threshold: float
    ) -> float:
        """
        计算连续窗口命中率
        在滑动窗口内，z-score 持续超过阈值的点的比例，反映异常的持续性
        """
        if len(z_scores) == 0:
            return 0.0
        
        hits = np.abs(z_scores) > threshold
        return float(np.sum(hits) / len(z_scores))
    
    def _compute_local_suggestion(self, features: AnomalyFeatures) -> str:
        """
        根据多维特征计算局部判据建议
        """
        if not self.enable_local_suggestion:
            return "normal"
        
        high_confidence_count = 0
        
        if features.hf_energy_ratio > 0.5:
            high_confidence_count += 1
        if features.consecutive_hit_rate > 0.8:
            high_confidence_count += 1
        if abs(features.z_score_max) > 10:
            high_confidence_count += 1
        if features.relative_deviation_rate > 0.1:
            high_confidence_count += 1
        
        if high_confidence_count >= 2:
            return "high_confidence_anomaly"
        elif high_confidence_count >= 1 or features.hf_energy_ratio > 0.3:
            return "potential_fluctuation"
        else:
            return "normal"
    
    def _predict_loess_fast(
        self, 
        x_history: np.ndarray, 
        y_history: np.ndarray,
        x_new: float
    ) -> Tuple[float, float]:
        """使用简化的 LOESS 预测（快速版本）"""
        n = len(x_history)
        
        if n < 3:
            return y_history[-1], np.std(y_history) if n > 1 else 0.1
        
        try:
            bandwidth = self.smoothing_factor * (x_history.max() - x_history.min() + 1e-6)
            weights = np.exp(-0.5 * ((x_history - x_new) / bandwidth) ** 2)
            weights_sum = weights.sum()
            
            if weights_sum < 1e-10:
                return y_history[-1], np.std(y_history)
            
            weights = weights / weights_sum
            
            y_pred = np.dot(weights, y_history)
            
            x_mean = np.dot(weights, x_history)
            x_centered = x_history - x_mean
            y_centered = y_history - y_pred
            
            wxx = np.dot(weights * x_centered, x_centered)
            wxy = np.dot(weights * x_centered, y_centered)
            
            if wxx > 1e-10:
                slope = wxy / wxx
                y_pred = y_pred + slope * (x_new - x_mean)
            
            residuals = y_history - (y_pred + slope * (x_history - x_mean) if wxx > 1e-10 else y_pred)
            pred_std = np.sqrt(np.dot(weights, residuals**2))
            
            return y_pred, max(pred_std, 1e-6)
            
        except Exception:
            return y_history[-1], np.std(y_history) if n > 1 else 0.1
    
    def _predict_loess(
        self, 
        x_history: np.ndarray, 
        y_history: np.ndarray,
        x_new: float
    ) -> Tuple[float, float]:
        """使用 LOESS 预测（保留原接口）"""
        return self._predict_loess_fast(x_history, y_history, x_new)
    
    def _estimate_robust_scale(self, residuals: np.ndarray) -> float:
        """使用 MAD 估计鲁棒尺度"""
        if len(residuals) == 0:
            return 1.0
        mad = np.median(np.abs(residuals - np.median(residuals)))
        return max(1.4826 * mad, 1e-6)
    
    def _detect_changepoint(
        self,
        y_history: np.ndarray,
        y_new: np.ndarray
    ) -> Optional[Tuple[float, str]]:
        """检测变点"""
        if len(y_history) < 3 or len(y_new) < 2:
            return None
        
        mean_before = np.mean(y_history[-min(10, len(y_history)):])
        mean_after = np.mean(y_new)
        std_before = np.std(y_history[-min(10, len(y_history)):])
        
        if std_before > 1e-10:
            t_stat = abs(mean_after - mean_before) / std_before
            if t_stat > 2.0:
                magnitude = mean_after - mean_before
                direction = "down" if magnitude < 0 else "up"
                return magnitude, direction
        
        return None
    
    def _is_converging_curve(
        self,
        x_history: np.ndarray,
        y_history: np.ndarray,
        x_new: np.ndarray,
        y_new: np.ndarray
    ) -> bool:
        """
        检测曲线是否呈现收敛趋势（增长放缓但仍在上升）
        
        收敛特征：
        1. 整体趋势向上（历史数据斜率为正）
        2. 斜率递减（二阶导数为负）
        3. 新数据仍在上升或持平
        """
        if len(y_history) < 5:
            return False
        
        n = len(y_history)
        mid = n // 2
        
        first_half_slope = (y_history[mid] - y_history[0]) / (x_history[mid] - x_history[0] + 1e-10)
        second_half_slope = (y_history[-1] - y_history[mid]) / (x_history[-1] - x_history[mid] + 1e-10)
        
        if first_half_slope <= 0:
            return False
        
        slope_decreasing = second_half_slope < first_half_slope * 0.8
        
        if len(y_new) >= 2:
            new_trend = y_new[-1] - y_new[0]
            new_not_dropping = new_trend >= -0.01
        else:
            new_not_dropping = y_new[0] >= y_history[-1] - 0.02
        
        return slope_decreasing and new_not_dropping
    
    def analyze_curve(
        self,
        legend: str,
        df_curve: pd.DataFrame,
        insight_sid: Optional[str] = None
    ) -> Optional[AnomalyAlert]:
        """
        分析单条曲线
        
        Args:
            legend: 曲线名称
            df_curve: 包含该曲线所有数据点的 DataFrame
            insight_sid: 图表 ID
            
        Returns:
            AnomalyAlert 或 None
        """
        df_curve = df_curve.sort_values('x').reset_index(drop=True)
        
        if 'is_new' not in df_curve.columns:
            return None
        
        history_df = df_curve[df_curve['is_new'] == 0]
        new_df = df_curve[df_curve['is_new'] == 1]
        
        if len(history_df) < self.min_history or len(new_df) < self.min_new_points:
            return None
        
        x_history = history_df['x'].values
        y_history = history_df['y'].values
        x_new = new_df['x'].values
        y_new = new_df['y'].values
        
        n_new = len(x_new)
        
        if n_new >= 3:
            hist_std = np.std(y_history[-min(50, len(y_history)):])
            hist_mean = np.mean(y_history[-min(20, len(y_history)):])
            new_mean = np.mean(y_new)
            new_std = np.std(y_new)
            
            mean_diff = abs(new_mean - hist_mean)
            if mean_diff < hist_std * 1.5 and new_std < hist_std * 1.5:
                return None
        y_preds = np.zeros(n_new)
        residuals = np.zeros(n_new)
        z_scores = np.zeros(n_new)
        
        bandwidth = self.smoothing_factor * (x_history.max() - x_history.min() + 1e-6)
        bandwidth_sq = bandwidth * bandwidth
        
        if NUMBA_AVAILABLE:
            for i in range(n_new):
                if i == 0:
                    x_train = x_history
                    y_train = y_history
                else:
                    x_train = np.concatenate([x_history, x_new[:i]])
                    y_train = np.concatenate([y_history, y_new[:i]])
                
                y_preds[i] = _predict_loess_numba(x_train, y_train, x_new[i], bandwidth_sq)
                residuals[i] = y_new[i] - y_preds[i]
                
                if i > 0:
                    robust_scale = _compute_median_absolute_deviation(residuals[:i+1])
                else:
                    robust_scale = max(0.1, abs(y_preds[i]) * 0.1)
                
                min_scale = max(0.01, abs(y_preds[i]) * 0.01)
                effective_scale = max(robust_scale, min_scale)
                z_scores[i] = residuals[i] / (effective_scale + 1e-10)
        else:
            for i in range(n_new):
                if i == 0:
                    x_train = x_history
                    y_train = y_history
                else:
                    x_train = np.append(x_history, x_new[:i])
                    y_train = np.append(y_history, y_new[:i])
                
                dist_sq = (x_train - x_new[i]) ** 2
                weights = np.exp(-0.5 * dist_sq / bandwidth_sq)
                weights_sum = weights.sum()
                
                if weights_sum > 1e-10:
                    weights /= weights_sum
                    y_preds[i] = np.dot(weights, y_train)
                    
                    x_mean = np.dot(weights, x_train)
                    x_centered = x_train - x_mean
                    y_centered = y_train - y_preds[i]
                    
                    wxx = np.dot(weights * x_centered, x_centered)
                    
                    if wxx > 1e-10:
                        wxy = np.dot(weights * x_centered, y_centered)
                        slope = wxy / wxx
                        y_preds[i] += slope * (x_new[i] - x_mean)
                else:
                    y_preds[i] = y_train[-1]
                
                residuals[i] = y_new[i] - y_preds[i]
                
                if i > 0:
                    mad = np.median(np.abs(residuals[:i+1] - np.median(residuals[:i+1])))
                    robust_scale = 1.4826 * mad if mad > 0 else 0.1
                else:
                    robust_scale = max(0.1, abs(y_preds[i]) * 0.1)
                
                min_scale = max(0.01, abs(y_preds[i]) * 0.01)
                effective_scale = max(robust_scale, min_scale)
                
                z_scores[i] = residuals[i] / (effective_scale + 1e-10)
        
        is_converging = self._is_converging_curve(x_history, y_history, x_new, y_new)
        
        abs_z_scores = np.abs(z_scores)
        abs_residuals = np.abs(residuals)
        rel_deviations = abs_residuals / (np.abs(y_preds) + 1e-10)
        
        z_threshold_adjusted = np.where(
            (is_converging) & (z_scores < 0),
            self.z_threshold * 3,
            self.z_threshold
        )
        abs_dev_threshold = np.where(
            (is_converging) & (z_scores < 0),
            self.min_abs_deviation * 3,
            self.min_abs_deviation
        )
        
        is_anomaly_mask = (
            (abs_z_scores > z_threshold_adjusted) &
            (abs_residuals >= abs_dev_threshold) &
            (rel_deviations >= self.min_rel_deviation)
        )
        
        consecutive = 0
        anomaly_start_idx = None
        first_z_score = None
        first_y_pred = None
        
        for i in range(len(z_scores)):
            if is_anomaly_mask[i]:
                if consecutive == 0:
                    anomaly_start_idx = i
                    first_z_score = z_scores[i]
                    first_y_pred = y_preds[i]
                consecutive += 1
                
                if consecutive >= self.consecutive_threshold:
                    cp_result = self._detect_changepoint(y_history, y_new[anomaly_start_idx:])
                    
                    if cp_result is not None:
                        magnitude, _ = cp_result
                        direction = "up" if first_z_score > 0 else "down"
                        anomaly_type = AnomalyType.STEP_UP if first_z_score > 0 else AnomalyType.STEP_DOWN
                        confidence = min(0.99, 0.5 + abs(first_z_score) / 20)
                        message = f"检测到{'上跳' if direction == 'up' else '下跳'}变点: x={x_new[anomaly_start_idx]:.2f}, 偏差={abs(y_new[anomaly_start_idx] - first_y_pred):.4f}"
                    else:
                        anomaly_type = AnomalyType.POINT
                        confidence = min(0.95, 0.3 + abs(first_z_score) / 15)
                        message = f"检测到连续异常点: 从 x={x_new[anomaly_start_idx]:.2f} 开始"
                    
                    max_abs_deviation = np.max(abs_residuals)
                    history_mean = np.mean(y_history)
                    
                    features = AnomalyFeatures(
                        robust_volatility_mad=self._compute_robust_volatility(residuals),
                        relative_deviation_rate=self._compute_relative_deviation(max_abs_deviation, history_mean),
                        hf_energy_ratio=self._compute_hf_energy_ratio(y_new),
                        consecutive_hit_rate=self._compute_consecutive_hit_rate(z_scores, self.z_threshold),
                        sample_size=len(y_new),
                        z_score_max=float(z_scores[np.argmax(abs_z_scores)]),
                        pearson_corr_with_peer=0.0
                    )
                    
                    local_suggestion = self._compute_local_suggestion(features)
                    
                    return AnomalyAlert(
                        legend=legend,
                        x_start=x_new[anomaly_start_idx],
                        x_end=x_new[-1],
                        y_observed=y_new[anomaly_start_idx],
                        y_predicted=first_y_pred,
                        z_score=first_z_score,
                        anomaly_type=anomaly_type,
                        confidence=confidence,
                        message=message,
                        insight_sid=insight_sid,
                        features=features,
                        local_suggestion=local_suggestion
                    )
            else:
                consecutive = 0
                anomaly_start_idx = None
        
        return None
    
    def analyze_snapshot(
        self,
        df: pd.DataFrame,
        legend_col: str = 'legend',
        x_col: str = 'x',
        y_col: str = 'y',
        is_new_col: str = 'is_new',
        insight_sid_col: str = 'insight_sid',
        n_jobs: int = 1
    ) -> List[AnomalyAlert]:
        """
        分析整个快照
        
        Args:
            n_jobs: 并行工作进程数，-1 表示使用所有 CPU 核心
        
        Returns:
            告警列表，按 z_score 绝对值降序排列（最显著的告警排在前面）
        """
        df = df.rename(columns={x_col: 'x', y_col: 'y', is_new_col: 'is_new'})
        
        legends = df[legend_col].unique()
        
        min_curves_for_parallel = 100
        
        if n_jobs == 1 or len(legends) < min_curves_for_parallel:
            alerts = []
            for legend in legends:
                df_curve = df[df[legend_col] == legend].copy()
                
                insight_sid = None
                if insight_sid_col in df.columns:
                    insight_sid = df_curve[insight_sid_col].iloc[0] if len(df_curve) > 0 else None
                
                alert = self.analyze_curve(legend, df_curve, insight_sid)
                if alert:
                    alerts.append(alert)
        else:
            if n_jobs == -1:
                n_jobs = min(cpu_count(), 8)
            
            curve_data = []
            for legend in legends:
                df_curve = df[df[legend_col] == legend].copy()
                insight_sid = None
                if insight_sid_col in df.columns:
                    insight_sid = df_curve[insight_sid_col].iloc[0] if len(df_curve) > 0 else None
                curve_data.append((legend, df_curve, insight_sid))
            
            analyze_func = partial(self._analyze_curve_wrapper)
            
            with Pool(processes=n_jobs) as pool:
                results = pool.map(analyze_func, curve_data, chunksize=max(1, len(curve_data) // (n_jobs * 4)))
            
            alerts = [alert for alert in results if alert is not None]
        
        alerts.sort(key=lambda x: abs(x.z_score), reverse=True)
        
        return alerts
    
    def _analyze_curve_wrapper(self, args: Tuple[str, pd.DataFrame, Optional[str]]) -> Optional[AnomalyAlert]:
        """多进程包装函数"""
        legend, df_curve, insight_sid = args
        return self.analyze_curve(legend, df_curve, insight_sid)
    
    def plot_curve(
        self,
        df_curve: pd.DataFrame,
        legend: str,
        output_path: str,
        alert: Optional[AnomalyAlert] = None
    ) -> str:
        """
        绘制单条曲线的分析图
        
        优化：
        1. 历史数据范围内使用 LOESS 拟合
        2. 外推部分使用线性外推（基于历史数据末端的斜率）
        3. 添加置信区间显示
        """
        df_curve = df_curve.sort_values('x').reset_index(drop=True)
        
        history_df = df_curve[df_curve['is_new'] == 0]
        new_df = df_curve[df_curve['is_new'] == 1]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if len(history_df) > 0:
            ax.plot(history_df['x'], history_df['y'], 'b-', linewidth=1.5, alpha=0.7)
            ax.scatter(history_df['x'], history_df['y'], c='blue', s=40, alpha=0.7, zorder=5,
                      label=f'历史数据点 (用于预测, n={len(history_df)})')
        
        if len(new_df) > 0:
            ax.plot(new_df['x'], new_df['y'], 'r-', linewidth=1.5, alpha=0.7)
            ax.scatter(new_df['x'], new_df['y'], c='red', s=60, alpha=0.8, zorder=6, marker='s',
                      label=f'新增数据点 (被检测, n={len(new_df)})')
        
        if len(history_df) >= 3:
            x_history = history_df['x'].values
            y_history = history_df['y'].values
            x_all = df_curve['x'].values
            
            try:
                # 1. 检查是否适合对数变换 (处理大幅度衰减曲线)
                use_log = False
                if y_history.min() > 1e-6:  # 避免 log(0)
                    y_ratio = y_history.max() / y_history.min()
                    # 如果动态范围大，且呈现衰减趋势
                    if y_ratio > 2.0 and y_history[0] > y_history[-1]:
                         use_log = True
                
                # 2. 准备训练数据
                y_train = np.log(y_history) if use_log else y_history
                
                history_range = x_history.max() - x_history.min()
                
                # 3. 基于变换后的数据判断曲线特征
                y_range = y_train.max() - y_train.min()
                y_early_change = abs(y_train[min(5, len(y_train)-1)] - y_train[0]) if len(y_train) > 1 else 0
                is_rapid_change = y_early_change > 0.5 * y_range if y_range > 0 else False
                
                # 4. 设置平滑参数
                if is_rapid_change:
                    base_smoothing = 0.1  # 变换后依然急剧变化，用小带宽
                else:
                    base_smoothing = self.smoothing_factor # 变换后平缓，用默认带宽
                
                x_smooth_history = np.linspace(x_history.min(), x_history.max(), 100)
                y_smooth_history = np.zeros_like(x_smooth_history)
                
                for i, x_pt in enumerate(x_smooth_history):
                    # 自适应带宽
                    if is_rapid_change:
                        relative_pos = (x_pt - x_history.min()) / (history_range + 1e-6)
                        adaptive_smoothing = base_smoothing + (self.smoothing_factor - base_smoothing) * relative_pos
                    else:
                        adaptive_smoothing = base_smoothing
                    
                    bandwidth = adaptive_smoothing * (history_range + 1e-6)
                    
                    # 计算权重
                    weights = np.exp(-0.5 * ((x_history - x_pt) / bandwidth) ** 2)
                    
                    # 避免权重过小
                    effective_n = np.sum(weights > 0.01)
                    if effective_n < 3:
                        bandwidth = bandwidth * 1.5
                        weights = np.exp(-0.5 * ((x_history - x_pt) / bandwidth) ** 2)
                    
                    weights = weights / weights.sum()
                    
                    # LOESS 核心逻辑
                    x_centered = x_history - np.average(x_history, weights=weights)
                    x_pt_centered = x_pt - np.average(x_history, weights=weights)
                    
                    W = np.diag(weights)
                    X = np.column_stack([np.ones(len(x_history)), x_centered])
                    
                    XtWX = X.T @ W @ X
                    XtWy = X.T @ W @ y_train  # 使用 y_train
                    
                    if np.linalg.cond(XtWX) < 1e10:
                        beta = np.linalg.solve(XtWX, XtWy)
                        val = beta[0] + beta[1] * x_pt_centered
                    else:
                        val = np.average(y_train, weights=weights)
                    
                    y_smooth_history[i] = val
                
                # 5. 还原数据
                if use_log:
                    y_smooth_history = np.exp(y_smooth_history)
                
                ax.plot(x_smooth_history, y_smooth_history, 'g-', linewidth=2.5, alpha=0.8,
                       label='LOESS拟合曲线 (基于历史数据)')
                
                if len(new_df) > 0 and x_all.max() > x_history.max():
                    n_end = min(5, len(x_smooth_history))
                    if n_end >= 2:
                        x_end = x_smooth_history[-n_end:]
                        y_end = y_smooth_history[-n_end:]
                        slope = np.polyfit(x_end, y_end, 1)[0]
                    else:
                        slope = 0
                    
                    y_at_boundary = y_smooth_history[-1]
                    x_boundary = x_history.max()
                    
                    x_extrap = np.linspace(x_boundary, x_all.max(), 50)
                    y_extrap = y_at_boundary + slope * (x_extrap - x_boundary)
                    
                    ax.plot(x_extrap, y_extrap, 'g--', linewidth=2.5, alpha=0.6,
                           label='线性外推预测')
                
                ax.axvline(x=x_history[-1], color='purple', linestyle=':', linewidth=2, alpha=0.8,
                          label='预测分界线 (历史|新增)')
            except Exception:
                pass
        
        if alert:
            ax.axvspan(alert.x_start, alert.x_end, alpha=0.15, color='red', label='异常区间')
        
        type_names = {
            'step_down': '下跳变点',
            'step_up': '上跳变点',
            'point': '点异常',
            'trend_change': '趋势变化'
        }
        
        if alert:
            type_name = type_names.get(alert.anomaly_type.value, alert.anomaly_type.value)
            title_line1 = f"异常检测告警: {type_name}"
        else:
            title_line1 = "曲线分析 (未检测到异常)"
        
        title_line2 = legend
        if len(title_line2) > 80:
            title_line2 = title_line2[:40] + '\n' + title_line2[40:80] + '...'
        elif len(title_line2) > 40:
            title_line2 = title_line2[:40] + '\n' + title_line2[40:]
        
        ax.set_title(f"{title_line1}\n{title_line2}", fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel('X (训练步数)', fontsize=11)
        ax.set_ylabel('Y (指标值)', fontsize=11)
        
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9, ncol=1,
                 bbox_to_anchor=(1.02, 1), borderaxespad=0)
        ax.grid(True, alpha=0.3)
        
        if alert:
            info_text = (
                f"【告警详情】\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"类型: {type_name}\n"
                f"位置: x={alert.x_start:.2f} ~ {alert.x_end:.2f}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"实际观测值: {alert.y_observed:.6f}\n"
                f"LOESS预测值: {alert.y_predicted:.6f}\n"
                f"偏差: {alert.y_observed - alert.y_predicted:.6f}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"z-score: {alert.z_score:.2f}\n"
                f"置信度: {alert.confidence:.1%}"
            )
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))
        
        explain_text = (
            "【图表说明】\n"
            "• 蓝色圆点: 历史数据 (用于训练LOESS模型)\n"
            "• 红色方块: 新增数据 (被检测的点)\n"
            "• 绿色实线: LOESS拟合 (基于历史数据)\n"
            "• 绿色虚线: 线性外推预测\n"
            "• 紫色竖线: 历史/新增分界线\n"
            "• 红色阴影: 异常区间"
        )
        ax.text(0.02, 0.02, explain_text, transform=ax.transAxes, fontsize=8,
               verticalalignment='bottom',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='orange'))
        
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return output_path


def find_optimal_threshold(
    df: pd.DataFrame,
    consecutive_threshold: int = 3,
    min_abs_deviation: float = 0.02,
    target_min: int = 2,
    target_max: int = 8,
    z_min: float = 2.5,
    z_max: float = 10.0,
    c_min: int = 2,
    c_max: int = 5,
    max_iterations: int = 20,
    verbose: bool = True,
    n_jobs: int = 1
) -> Tuple[float, int, List[AnomalyAlert]]:
    """
    使用二分查找找到最优的 z_threshold 和 consecutive_threshold，使告警数量在目标范围内
    
    Args:
        df: 输入数据
        consecutive_threshold: 初始连续点数阈值
        min_abs_deviation: 最小绝对偏差阈值
        target_min: 目标告警数量下限
        target_max: 目标告警数量上限
        z_min: z_threshold 搜索下限
        z_max: z_threshold 搜索上限
        c_min: consecutive_threshold 搜索下限
        c_max: consecutive_threshold 搜索上限
        max_iterations: 最大迭代次数
        verbose: 是否打印详细信息
        
    Returns:
        (最优 z_threshold, 最优 consecutive_threshold, 告警列表)
    """
    def count_alerts(z_threshold: float, c_threshold: int) -> Tuple[int, List[AnomalyAlert]]:
        analyzer = SingleSnapshotAnalyzer(
            z_threshold=z_threshold,
            consecutive_threshold=c_threshold,
            min_abs_deviation=min_abs_deviation
        )
        alerts = analyzer.analyze_snapshot(df, n_jobs=n_jobs)
        return len(alerts), alerts
    
    best_z = z_min
    best_c = consecutive_threshold
    best_alerts = []
    best_count = 0
    
    for c_threshold in range(c_max, c_min - 1, -1):
        low, high = z_min, z_max
        
        count_at_min, alerts_at_min = count_alerts(z_min, c_threshold)
        if target_min <= count_at_min <= target_max:
            if verbose:
                print(f"  z={z_min:.2f}, c={c_threshold} 时告警数={count_at_min}，在目标范围内")
            return z_min, c_threshold, alerts_at_min
        
        if count_at_min < target_min:
            if count_at_min > best_count:
                best_z, best_c, best_alerts, best_count = z_min, c_threshold, alerts_at_min, count_at_min
            continue
        
        count_at_max, alerts_at_max = count_alerts(z_max, c_threshold)
        if target_min <= count_at_max <= target_max:
            if verbose:
                print(f"  z={z_max:.2f}, c={c_threshold} 时告警数={count_at_max}，在目标范围内")
            return z_max, c_threshold, alerts_at_max
        
        if count_at_max > target_max:
            if verbose:
                print(f"  c={c_threshold}: z_max={z_max:.2f} 时告警数={count_at_max} 仍然过多，跳过")
            continue
        
        if verbose:
            print(f"  c={c_threshold}: 二分查找 z_threshold in [{z_min:.2f}, {z_max:.2f}]")
        
        for i in range(max_iterations):
            mid = (low + high) / 2
            count, alerts = count_alerts(mid, c_threshold)
            
            if verbose:
                print(f"    迭代 {i+1}: z={mid:.2f}, 告警数={count}")
            
            if target_min <= count <= target_max:
                return mid, c_threshold, alerts
            
            if count > target_max:
                low = mid
            else:
                high = mid
                if count > best_count:
                    best_z, best_c, best_alerts, best_count = mid, c_threshold, alerts, count
            
            if high - low < 0.1:
                break
    
    if verbose:
        if best_count > 0:
            print(f"  未找到目标范围内的参数，返回最接近的结果: z={best_z:.2f}, c={best_c}, 告警数={best_count}")
        else:
            print(f"  未检测到目标范围内的告警配置")
            print(f"  建议：1) 增加 --target-max 参数以接受更多告警")
            print(f"        2) 使用固定阈值模式 --z-threshold 3.0 --consecutive 3")
    
    if best_count == 0:
        print(f"  警告：所有尝试的参数都未检测到告警，尝试使用宽松阈值...")
        final_z, final_c = z_min, c_min
        count, alerts = count_alerts(final_z, final_c)
        if verbose:
            print(f"  使用宽松阈值: z={final_z:.2f}, c={final_c}, 告警数={count}")
        return final_z, final_c, alerts
    
    return best_z, best_c, best_alerts


def write_alerts_csv(alerts: List[AnomalyAlert], output_path: str) -> None:
    """将告警列表写入 CSV 文件"""
    if not alerts:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write("legend,insight_sid,type,x_start,x_end,message,robust_volatility_mad,relative_deviation_rate,hf_energy_ratio,consecutive_hit_rate,sample_size,z_score_max,pearson_corr_with_peer,local_suggestion\n")
        return
    
    fieldnames = [
        'legend', 'insight_sid', 'type', 'x_start', 'x_end', 'message',
        'robust_volatility_mad', 'relative_deviation_rate', 'hf_energy_ratio',
        'consecutive_hit_rate', 'sample_size', 'z_score_max', 'pearson_corr_with_peer',
        'local_suggestion'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for a in alerts:
            features = a.features if a.features else AnomalyFeatures()
            row = {
                'legend': a.legend,
                'insight_sid': a.insight_sid or '',
                'type': a.anomaly_type.value,
                'x_start': f"{a.x_start:.2f}",
                'x_end': f"{a.x_end:.2f}",
                'message': a.message,
                'robust_volatility_mad': f"{features.robust_volatility_mad:.4f}",
                'relative_deviation_rate': f"{features.relative_deviation_rate:.4f}",
                'hf_energy_ratio': f"{features.hf_energy_ratio:.4f}",
                'consecutive_hit_rate': f"{features.consecutive_hit_rate:.4f}",
                'sample_size': features.sample_size,
                'z_score_max': f"{features.z_score_max:.2f}",
                'pearson_corr_with_peer': f"{features.pearson_corr_with_peer:.4f}",
                'local_suggestion': a.local_suggestion
            }
            writer.writerow(row)


def write_summary_txt(
    input_file: str,
    total_curves: int,
    total_alerts: int,
    z_threshold: float,
    consecutive_threshold: int,
    output_path: str
) -> None:
    """写入摘要文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"total_curves={total_curves},total_alerts={total_alerts},z_threshold={z_threshold:.2f},consecutive_threshold={consecutive_threshold}\n")


def run_single_analysis(
    input_csv: str,
    output_path: str = None,
    output_plot_dir: str = None,
    output_format: str = 'csv',
    z_threshold: float = 4.0,
    consecutive_threshold: int = 3,
    min_abs_deviation: float = 0.02,
    min_rel_deviation: float = 0.03,
    min_new_points: int = 2,
    enable_local_suggestion: bool = True,
    auto_threshold: bool = False,
    target_min: int = 2,
    target_max: int = 8,
    insight_sids: List[str] = None,
    legends: List[str] = None,
    verbose: bool = True,
    n_jobs: int = 1
) -> Dict[str, Any]:
    """
    对单个 CSV 快照进行异常检测
    
    Args:
        input_csv: 输入 CSV 文件路径
        output_path: 输出结果路径（不含扩展名，自动根据 output_format 添加）
        output_plot_dir: 输出图片目录
        output_format: 输出格式 ('csv', 'json', 'both')
        z_threshold: z-score 阈值
        consecutive_threshold: 连续点数阈值
        min_abs_deviation: 最小绝对偏差阈值
        min_new_points: 最少新增数据点数量
        enable_local_suggestion: 是否启用局部判据建议
        auto_threshold: 是否自动调整阈值以获得目标数量的告警
        target_min: 自动调整时的目标告警数量下限
        target_max: 自动调整时的目标告警数量上限
        insight_sids: 只关注的 insight_sid 列表，为空则分析所有曲线
        legends: 只关注的 legend 列表，为空则分析所有曲线
        verbose: 是否打印详细信息
        
    Returns:
        分析结果字典
    """
    if verbose:
        print(f"[性能优化] 正在读取 CSV...")
    df = pd.read_csv(input_csv, dtype={'is_new': 'int8'})
    
    original_curves = df['legend'].nunique()
    
    if insight_sids and 'insight_sid' in df.columns:
        df = df[df['insight_sid'].isin(insight_sids)]
        if verbose:
            print(f"过滤 insight_sid: {len(insight_sids)} 个")
            print(f"  原始曲线数: {original_curves}, 过滤后: {df['legend'].nunique()}")
    
    if legends:
        df = df[df['legend'].isin(legends)]
        if verbose:
            print(f"过滤 legend: {len(legends)} 个")
            print(f"  原始曲线数: {original_curves}, 过滤后: {df['legend'].nunique()}")
    
    if verbose:
        print(f"读取 CSV: {input_csv}")
        print(f"总行数: {len(df)}")
        print(f"曲线数: {df['legend'].nunique()}")
        if 'is_new' in df.columns:
            print(f"历史数据: {(df['is_new'] == 0).sum()} 行")
            print(f"新增数据: {(df['is_new'] == 1).sum()} 行")
    
    if verbose and n_jobs != 1:
        total_curves = df['legend'].nunique()
        min_curves_for_parallel = 100
        if total_curves >= min_curves_for_parallel:
            actual_jobs = n_jobs if n_jobs > 0 else min(cpu_count(), 8)
            print(f"[性能优化] 使用多进程模式: {actual_jobs} 个进程 ({total_curves} 条曲线)")
        else:
            print(f"[性能优化] 曲线数量较少 ({total_curves} < {min_curves_for_parallel})，使用单进程模式")
    
    if auto_threshold:
        if verbose:
            print(f"\n[性能优化] 自动阈值调整模式: 目标告警数量 {target_min}~{target_max}")
        z_threshold, consecutive_threshold, alerts = find_optimal_threshold(
            df=df,
            consecutive_threshold=consecutive_threshold,
            min_abs_deviation=min_abs_deviation,
            target_min=target_min,
            target_max=target_max,
            verbose=verbose,
            n_jobs=n_jobs
        )
        if verbose:
            print(f"  最终选择: z_threshold={z_threshold:.2f}, consecutive={consecutive_threshold}, 告警数={len(alerts)}")
    else:
        if verbose:
            print(f"\n[性能优化] 开始异常检测...")
        analyzer = SingleSnapshotAnalyzer(
            z_threshold=z_threshold,
            consecutive_threshold=consecutive_threshold,
            min_abs_deviation=min_abs_deviation,
            min_rel_deviation=min_rel_deviation,
            min_new_points=min_new_points,
            enable_local_suggestion=enable_local_suggestion
        )
        alerts = analyzer.analyze_snapshot(df, n_jobs=n_jobs)
    
    analyzer = SingleSnapshotAnalyzer(
        z_threshold=z_threshold,
        consecutive_threshold=consecutive_threshold,
        min_abs_deviation=min_abs_deviation,
        min_rel_deviation=min_rel_deviation,
        min_new_points=min_new_points,
        enable_local_suggestion=enable_local_suggestion
    )
    
    if verbose:
        print(f"\n检测到 {len(alerts)} 个告警")
    
    if output_plot_dir and len(alerts) > 0:
        if verbose:
            print(f"\n[性能优化] 正在生成告警图片...")
        os.makedirs(output_plot_dir, exist_ok=True)
        
        for i, alert in enumerate(alerts):
            df_curve = df[df['legend'] == alert.legend].copy()
            safe_name = alert.legend.replace('/', '_').replace('\\', '_').replace('【', '').replace('】', '').replace(' ', '_').replace('[', '').replace(']', '')[:50]
            plot_path = os.path.join(output_plot_dir, f"alert_{i+1:03d}_{safe_name}_{alert.anomaly_type.value}.png")
            analyzer.plot_curve(df_curve, alert.legend, plot_path, alert)
            if verbose:
                print(f"  -> 生成告警图片: {os.path.basename(plot_path)}")
    
    total_curves = df['legend'].nunique()
    
    result = {
        'input_file': input_csv,
        'total_curves': total_curves,
        'total_alerts': len(alerts),
        'parameters': {
            'z_threshold': z_threshold,
            'consecutive_threshold': consecutive_threshold,
            'min_abs_deviation': min_abs_deviation
        },
        'alerts': [
            {
                'legend': a.legend,
                'insight_sid': a.insight_sid,
                'type': a.anomaly_type.value,
                'x_start': a.x_start,
                'x_end': a.x_end,
                'y_observed': a.y_observed,
                'y_predicted': a.y_predicted,
                'z_score': a.z_score,
                'confidence': a.confidence,
                'message': a.message,
                'features': asdict(a.features) if a.features else {},
                'local_suggestion': a.local_suggestion
            }
            for a in alerts
        ]
    }
    
    if output_path:
        output_pathobj = Path(output_path)
        if output_pathobj.suffix:
            base_path = str(output_pathobj.with_suffix(''))
        else:
            base_path = output_path
        
        if output_format in ('csv', 'both'):
            csv_path = f"{base_path}.csv"
            summary_path = f"{base_path}_summary.txt"
            write_alerts_csv(alerts, csv_path)
            write_summary_txt(input_csv, total_curves, len(alerts), z_threshold, consecutive_threshold, summary_path)
            if verbose:
                print(f"\n结果已保存到: {csv_path}")
                print(f"摘要已保存到: {summary_path}")
        
        if output_format in ('json', 'both'):
            json_path = f"{base_path}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if verbose:
                print(f"\n结果已保存到: {json_path}")
    
    return result


def main():
    start_time = time.time()
    
    parser = argparse.ArgumentParser(
        description='单次异常检测脚本：对单个 CSV 快照进行异常检测'
    )
    parser.add_argument(
        'input',
        type=str,
        help='输入 CSV 文件路径'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='输出结果路径（不含扩展名）'
    )
    parser.add_argument(
        '--output-format', '-f',
        type=str,
        choices=['csv', 'json', 'both'],
        default='csv',
        help='输出格式 (默认: csv)'
    )
    parser.add_argument(
        '--plot-dir', '-p',
        type=str,
        default=None,
        help='输出图片目录'
    )
    parser.add_argument(
        '--z-threshold', '-z',
        type=float,
        default=4.0,
        help='z-score 阈值 (默认: 4.0)'
    )
    parser.add_argument(
        '--consecutive', '-c',
        type=int,
        default=3,
        help='连续点数阈值 (默认: 3)'
    )
    parser.add_argument(
        '--min-deviation', '-m',
        type=float,
        default=0.02,
        help='最小绝对偏差阈值 (默认: 0.02)'
    )
    parser.add_argument(
        '--min-rel-deviation', '-r',
        type=float,
        default=0.03,
        help='最小相对偏差阈值 (默认: 0.03)'
    )
    parser.add_argument(
        '--min-new-points',
        type=int,
        default=2,
        help='最少新增数据点数量 (默认: 2)'
    )
    parser.add_argument(
        '--no-local-suggestion',
        action='store_true',
        help='关闭局部判据建议'
    )
    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='自动调整阈值模式：使用二分查找找到合适的 z_threshold 使告警数量在目标范围内'
    )
    parser.add_argument(
        '--target-min',
        type=int,
        default=2,
        help='自动模式下的目标告警数量下限 (默认: 2)'
    )
    parser.add_argument(
        '--target-max',
        type=int,
        default=80,
        help='自动模式下的目标告警数量上限 (默认: 80)'
    )
    parser.add_argument(
        '--insight-sids', '-i',
        type=str,
        nargs='+',
        default=None,
        help='只关注的 insight_sid 列表，多个用空格分隔'
    )
    parser.add_argument(
        '--legends', '-l',
        type=str,
        nargs='+',
        default=None,
        help='只关注的 legend 列表，多个用空格分隔'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安静模式'
    )
    parser.add_argument(
        '--jobs', '-j',
        type=int,
        default=1,
        help='并行进程数，-1 表示使用所有 CPU 核心 (默认: 1, 单进程)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input).resolve()
    
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        return
    
    output_path = args.output
    if output_path:
        output_path = str(Path(output_path).resolve())
    
    plot_dir = args.plot_dir
    if plot_dir:
        plot_dir = str(Path(plot_dir).resolve())
    result = run_single_analysis(
        input_csv=str(input_path),
        output_path=output_path,
        output_plot_dir=plot_dir,
        output_format=args.output_format,
        z_threshold=args.z_threshold,
        consecutive_threshold=args.consecutive,
        min_abs_deviation=args.min_deviation,
        min_rel_deviation=args.min_rel_deviation,
        min_new_points=args.min_new_points,
        enable_local_suggestion=not args.no_local_suggestion,
        auto_threshold=args.auto,
        target_min=args.target_min,
        target_max=args.target_max,
        insight_sids=args.insight_sids,
        legends=args.legends,
        verbose=not args.quiet,
        n_jobs=args.jobs
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    if not args.quiet:
        print(f"\n=== 分析完成 ===")
        print(f"总告警数: {result['total_alerts']}")
        if args.auto:
            print(f"使用参数: z_threshold={result['parameters']['z_threshold']:.2f}, consecutive={result['parameters']['consecutive_threshold']}")
        
        if result['alerts']:
            print("\n告警详情 (按显著程度排序):")
            for i, alert in enumerate(result['alerts'], 1):
                print(f"  {i}. [{alert['type']}] {alert['legend'][:60]}")
                print(f"     位置: x={alert['x_start']:.2f} ~ {alert['x_end']:.2f}")
                print(f"     z-score: {alert['z_score']:.2f}, 置信度: {alert['confidence']:.1%}")
                print(f"     建议: {alert['local_suggestion']}")
                print(f"     {alert['message']}")
        
        print(f"\n代码执行时间: {execution_time:.2f} 秒")
    else:
        print(f"代码执行时间: {execution_time:.2f} 秒")


if __name__ == '__main__':
    main()