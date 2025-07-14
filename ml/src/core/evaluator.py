# ml-service/src/evaluation/evaluator.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BasketPredictionEvaluator:
    """
Comprehensive evaluation framework for basket prediction
    """
    
    def __init__(self):
        self.evaluation_results = {}
        self.comparison_results = {}
        
    def evaluate_model(self, predictions: List[Dict], k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Evaluate model predictions with comprehensive metrics
        """
        logger.info("Starting model evaluation...")
        
        # Initialize metric collectors
        metrics = {
            'precision': {k: [] for k in k_values},
            'recall': {k: [] for k in k_values},
            'f1_score': {k: [] for k in k_values},
            'ndcg': {k: [] for k in k_values},
            'hit_rate': {k: 0 for k in k_values},
            'coverage': {k: set() for k in k_values},
            'diversity': {k: [] for k in k_values}
        }
        
        total_users = len(predictions)
        
        for pred in predictions:
            user_id = pred['user_id']
            predicted = pred['predicted_products']
            actual = pred['actual_products']
            scores = pred.get('scores', [1.0] * len(predicted))
            
            if len(actual) == 0:
                continue
            
            for k in k_values:
                # Get top-k predictions
                top_k_pred = predicted[:k]
                top_k_scores = scores[:k]
                
                # Precision@k
                precision = self._calculate_precision(top_k_pred, actual)
                metrics['precision'][k].append(precision)
                
                # Recall@k
                recall = self._calculate_recall(top_k_pred, actual)
                metrics['recall'][k].append(recall)
                
                # F1-Score@k
                f1 = self._calculate_f1(precision, recall)
                metrics['f1_score'][k].append(f1)
                
                # NDCG@k
                ndcg = self._calculate_ndcg(top_k_pred, actual, k)
                metrics['ndcg'][k].append(ndcg)
                
                # Hit Rate
                if len(set(top_k_pred) & set(actual)) > 0:
                    metrics['hit_rate'][k] += 1
                
                # Coverage
                metrics['coverage'][k].update(top_k_pred)
                
                # Diversity
                diversity = len(set(top_k_pred)) / k if k > 0 else 0
                metrics['diversity'][k].append(diversity)
        
        # Calculate final metrics
        results = {}
        for k in k_values:
            results[f'k={k}'] = {
                'precision': np.mean(metrics['precision'][k]) if metrics['precision'][k] else 0,
                'recall': np.mean(metrics['recall'][k]) if metrics['recall'][k] else 0,
                'f1_score': np.mean(metrics['f1_score'][k]) if metrics['f1_score'][k] else 0,
                'ndcg': np.mean(metrics['ndcg'][k]) if metrics['ndcg'][k] else 0,
                'hit_rate': metrics['hit_rate'][k] / total_users if total_users > 0 else 0,
                'coverage': len(metrics['coverage'][k]),
                'avg_diversity': np.mean(metrics['diversity'][k]) if metrics['diversity'][k] else 0
            }
        
        # Calculate overall statistics
        all_actual_products = set()
        all_predicted_products = set()
        basket_sizes = []
        
        for pred in predictions:
            all_actual_products.update(pred['actual_products'])
            all_predicted_products.update(pred['predicted_products'][:max(k_values)])
            basket_sizes.append(len(pred['actual_products']))
        
        results['overall'] = {
            'total_users': total_users,
            'unique_actual_products': len(all_actual_products),
            'unique_predicted_products': len(all_predicted_products),
            'avg_basket_size': np.mean(basket_sizes) if basket_sizes else 0,
            'std_basket_size': np.std(basket_sizes) if basket_sizes else 0
        }
        
        self.evaluation_results = results
        logger.info("Evaluation completed")
        
        return results
    
    def _calculate_precision(self, predicted: List[int], actual: List[int]) -> float:
        """Calculate precision"""
        if len(predicted) == 0:
            return 0.0
        return len(set(predicted) & set(actual)) / len(predicted)
    
    def _calculate_recall(self, predicted: List[int], actual: List[int]) -> float:
        """Calculate recall"""
        if len(actual) == 0:
            return 0.0
        return len(set(predicted) & set(actual)) / len(actual)
    
    def _calculate_f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)
    
    def _calculate_ndcg(self, predicted: List[int], actual: List[int], k: int) -> float:
        """Calculate NDCG@k"""
        dcg = 0.0
        for i, item in enumerate(predicted[:k]):
            if item in actual:
                dcg += 1.0 / np.log2(i + 2)
        
        # Ideal DCG
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(actual), k)))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def compare_methods(self, methods_results: Dict[str, List[Dict]], 
                       k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Compare multiple methods (for benchmarking)
        """
        comparison = {}
        
        for method_name, predictions in methods_results.items():
            method_results = self.evaluate_model(predictions, k_values)
            comparison[method_name] = method_results
        
        self.comparison_results = comparison
        return comparison
    
    def generate_evaluation_report(self, output_dir: str, include_plots: bool = True):
        """Generate comprehensive evaluation report"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save numerical results
        report = {
            'evaluation_date': datetime.now().isoformat(),
            'results': self.evaluation_results,
            'comparison': self.comparison_results if self.comparison_results else None
        }
        
        with open(os.path.join(output_dir, 'evaluation_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate plots if requested
        if include_plots and self.evaluation_results:
            self._generate_plots(output_dir)
        
        # Generate markdown report
        self._generate_markdown_report(output_dir)
        
        logger.info(f"Evaluation report saved to {output_dir}")
    
    def _generate_plots(self, output_dir: str):
        """Generate visualization plots"""
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Extract metrics for plotting
        k_values = []
        precisions = []
        recalls = []
        f1_scores = []
        ndcgs = []
        hit_rates = []
        
        for k_str, metrics in self.evaluation_results.items():
            if k_str.startswith('k='):
                k = int(k_str.split('=')[1])
                k_values.append(k)
                precisions.append(metrics['precision'])
                recalls.append(metrics['recall'])
                f1_scores.append(metrics['f1_score'])
                ndcgs.append(metrics['ndcg'])
                hit_rates.append(metrics['hit_rate'])
        
        # Plot 1: Metrics vs K
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Precision, Recall, F1
        ax1.plot(k_values, precisions, 'o-', label='Precision', linewidth=2, markersize=8)
        ax1.plot(k_values, recalls, 's-', label='Recall', linewidth=2, markersize=8)
        ax1.plot(k_values, f1_scores, '^-', label='F1-Score', linewidth=2, markersize=8)
        ax1.set_xlabel('K')
        ax1.set_ylabel('Score')
        ax1.set_title('Precision, Recall, and F1-Score @ K')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # NDCG
        ax2.plot(k_values, ndcgs, 'o-', color='green', linewidth=2, markersize=8)
        ax2.set_xlabel('K')
        ax2.set_ylabel('NDCG')
        ax2.set_title('NDCG @ K')
        ax2.grid(True, alpha=0.3)
        
        # Hit Rate
        ax3.plot(k_values, hit_rates, 'o-', color='orange', linewidth=2, markersize=8)
        ax3.set_xlabel('K')
        ax3.set_ylabel('Hit Rate')
        ax3.set_title('Hit Rate @ K')
        ax3.grid(True, alpha=0.3)
        
        # Metrics Table
        ax4.axis('tight')
        ax4.axis('off')
        
        # Create metrics table
        headers = ['K', 'Precision', 'Recall', 'F1-Score', 'NDCG', 'Hit Rate']
        table_data = []
        for i, k in enumerate(k_values):
            row = [
                k,
                f"{precisions[i]:.3f}",
                f"{recalls[i]:.3f}",
                f"{f1_scores[i]:.3f}",
                f"{ndcgs[i]:.3f}",
                f"{hit_rates[i]:.3f}"
            ]
            table_data.append(row)
        
        table = ax4.table(cellText=table_data, colLabels=headers, 
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'evaluation_metrics.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Comparison plot if available
        if self.comparison_results:
            self._generate_comparison_plot(output_dir)
    
    def _generate_comparison_plot(self, output_dir: str):
        """Generate method comparison plot"""
        methods = list(self.comparison_results.keys())
        metrics = ['precision', 'recall', 'f1_score', 'ndcg', 'hit_rate']
        k = 10  # Use k=10 for comparison
        
        # Extract data
        data = []
        for method in methods:
            method_metrics = []
            for metric in metrics:
                value = self.comparison_results[method].get(f'k={k}', {}).get(metric, 0)
                method_metrics.append(value)
            data.append(method_metrics)
        
        # Create grouped bar chart
        x = np.arange(len(metrics))
        width = 0.8 / len(methods)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for i, (method, values) in enumerate(zip(methods, data)):
            offset = width * i - (width * len(methods) / 2)
            ax.bar(x + offset, values, width, label=method)
        
        ax.set_xlabel('Metrics')
        ax.set_ylabel('Score')
        ax.set_title(f'Method Comparison @ K={k}')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'method_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_markdown_report(self, output_dir: str):
        """Generate markdown format report"""
        report_content = "# Basket Prediction Evaluation Report\n\n"
        report_content += f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if self.evaluation_results:
            report_content += "## Model Performance\n\n"
            
            # Overall statistics
            if 'overall' in self.evaluation_results:
                overall = self.evaluation_results['overall']
                report_content += "### Overall Statistics\n\n"
                report_content += f"- Total Users: {overall['total_users']}\n"
                report_content += f"- Unique Actual Products: {overall['unique_actual_products']}\n"
                report_content += f"- Unique Predicted Products: {overall['unique_predicted_products']}\n"
                report_content += f"- Average Basket Size: {overall['avg_basket_size']:.2f} ± {overall['std_basket_size']:.2f}\n\n"
            
            # Metrics table
            report_content += "### Performance Metrics\n\n"
            report_content += "| K | Precision | Recall | F1-Score | NDCG | Hit Rate | Coverage | Diversity |\n"
            report_content += "|---|-----------|--------|----------|------|----------|----------|----------|\n"
            
            for k_str, metrics in self.evaluation_results.items():
                if k_str.startswith('k='):
                    k = k_str.split('=')[1]
                    report_content += f"| {k} | "
                    report_content += f"{metrics['precision']:.3f} | "
                    report_content += f"{metrics['recall']:.3f} | "
                    report_content += f"{metrics['f1_score']:.3f} | "
                    report_content += f"{metrics['ndcg']:.3f} | "
                    report_content += f"{metrics['hit_rate']:.3f} | "
                    report_content += f"{metrics['coverage']} | "
                    report_content += f"{metrics['avg_diversity']:.3f} |\n"
            
            report_content += "\n"
        
        # Method comparison if available
        if self.comparison_results:
            report_content += "## Method Comparison\n\n"
            
            # Create comparison table for k=10
            k = 10
            report_content += f"### Performance @ K={k}\n\n"
            report_content += "| Method | Precision | Recall | F1-Score | NDCG | Hit Rate |\n"
            report_content += "|--------|-----------|--------|----------|------|----------|\n"
            
            for method, results in self.comparison_results.items():
                metrics = results.get(f'k={k}', {})
                report_content += f"| {method} | "
                report_content += f"{metrics.get('precision', 0):.3f} | "
                report_content += f"{metrics.get('recall', 0):.3f} | "
                report_content += f"{metrics.get('f1_score', 0):.3f} | "
                report_content += f"{metrics.get('ndcg', 0):.3f} | "
                report_content += f"{metrics.get('hit_rate', 0):.3f} |\n"
        
        # Save report
        with open(os.path.join(output_dir, 'evaluation_report.md'), 'w') as f:
            f.write(report_content)
    
    def calculate_online_metrics(self, user_feedback: List[Dict]) -> Dict[str, float]:
        """
        Calculate online metrics from user feedback
        """
        total_baskets = len(user_feedback)
        accepted_baskets = sum(1 for fb in user_feedback if fb.get('accepted', False))
        
        total_items_predicted = 0
        total_items_accepted = 0
        edit_distances = []
        
        for feedback in user_feedback:
            predicted_items = set(feedback.get('predicted_items', []))
            accepted_items = set(feedback.get('accepted_items', []))
            
            total_items_predicted += len(predicted_items)
            total_items_accepted += len(accepted_items)
            
            # Calculate edit distance
            added = len(accepted_items - predicted_items)
            removed = len(predicted_items - accepted_items)
            edit_distances.append(added + removed)
        
        return {
            'auto_cart_acceptance_rate': accepted_baskets / total_baskets if total_baskets > 0 else 0,
            'item_acceptance_rate': total_items_accepted / total_items_predicted if total_items_predicted > 0 else 0,
            'avg_edit_distance': np.mean(edit_distances) if edit_distances else 0,
            'total_baskets_evaluated': total_baskets
        }
