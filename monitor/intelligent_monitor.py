#!/usr/bin/env python3
"""智能监控系统 - 实时监控Token使用，智能预警"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

class IntelligentMonitor:
    """智能监控器 - 实时监控Token使用并提供预警"""

    def __init__(self, data_dir='./data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.usage_file = self.data_dir / 'usage_log.json'
        self.alerts_file = self.data_dir / 'alerts.json'

        self.usage_history = self._load_usage()
        self.alerts = self._load_alerts()

        self.hourly_limit = 5000
        self.daily_limit = 50000
        self.alert_cooldown = 3600 # 1小时内不重复告警

    def _load_usage(self) -> List[Dict]:
        """加载使用记录"""
        if self.usage_file.exists():
            with open(self.usage_file) as f:
                return json.load(f)
        return []

    def _load_alerts(self) -> List[Dict]:
        """加载告警记录"""
        if self.alerts_file.exists():
            with open(self.alerts_file) as f:
                return json.load(f)
        return []

    def _save_usage(self):
        """保存使用记录"""
        cutoff = datetime.now() - timedelta(days=30)
        recent = [u for u in self.usage_history if datetime.fromisoformat(u['timestamp']) > cutoff]

        with open(self.usage_file, 'w') as f:
            json.dump(recent, f, indent=2)

    def record_usage(self, operation: str, tokens: int, context: str = ''):
        """记录Token使用"""
        entry = {'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'tokens': tokens,
            'context': context}

        self.usage_history.append(entry)
        self._save_usage()

        self._check_alerts()

    def _check_alerts(self):
        """检查是否需要触发告警"""
        now = datetime.now()

        hour_ago = now - timedelta(hours=1)
        hour_usage = sum(u['tokens'] for u in self.usage_history
                        if datetime.fromisoformat(u['timestamp']) > hour_ago)

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_usage = sum(u['tokens'] for u in self.usage_history
                       if datetime.fromisoformat(u['timestamp']) > today_start)

        if hour_usage > self.hourly_limit:
            self._trigger_alert('hourly_limit', hour_usage, self.hourly_limit)

        if day_usage > self.daily_limit:
            self._trigger_alert('daily_limit', day_usage, self.daily_limit)

    def _trigger_alert(self, alert_type: str, current: int, limit: int):
        """触发告警"""
        now = datetime.now()

        recent_alerts = [a for a in self.alerts
                        if a['type'] == alert_type
                        and datetime.fromisoformat(a['timestamp']) > now - timedelta(seconds=self.alert_cooldown)]

        if recent_alerts:
            return # 冷却期内不重复告警

        alert = {'timestamp': now.isoformat(),
            'type': alert_type,
            'current': current,
            'limit': limit,
            'message': f"Token使用超过{alert_type}: {current} > {limit}"}

        self.alerts.append(alert)

        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)

        print(f"⚠️ 告警: {alert['message']}")

    def get_usage_stats(self, period: str = 'day') -> Dict[str, Any]:
        """获取使用统计"""
        now = datetime.now()

        if period == 'hour':
            cutoff = now - timedelta(hours=1)
        elif period == 'day':
            cutoff = now - timedelta(days=1)
        elif period == 'week':
            cutoff = now - timedelta(weeks=1)
        else:
            cutoff = now - timedelta(days=1)

        recent_usage = [u for u in self.usage_history
                       if datetime.fromisoformat(u['timestamp']) > cutoff]

        total_tokens = sum(u['tokens'] for u in recent_usage)
        operation_count = len(recent_usage)

        by_operation = {}
        for u in recent_usage:
            op = u['operation']
            by_operation[op] = by_operation.get(op, 0) + u['tokens']

        return {'period': period,
            'total_tokens': total_tokens,
            'operation_count': operation_count,
            'avg_per_operation': total_tokens // operation_count if operation_count > 0 else 0,
            'by_operation': by_operation,
            'budget': {'daily': self.daily_limit, 'hourly': self.hourly_limit}}

    def start_watching(self, target_path: str, interval: int = 60):
        """启动监控模式"""
        print(f"👁️ 开始监控: {target_path}")
        print(f" 检查间隔: {interval}秒")
        print(f" 日限额: {self.daily_limit:,} tokens")
        print(f" 小时限额: {self.hourly_limit:,} tokens")
        print(" 按 Ctrl+C 停止监控\n")

        try:
            while True:
                time.sleep(interval)

                from analyzer.unified_analyzer import UnifiedAnalyzer
                analyzer = UnifiedAnalyzer()

                result = analyzer.analyze(target_path)

                self.record_usage('analysis', result.get('total_tokens', 0), target_path)

                stats = self.get_usage_stats('hour')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"分析Token: {result.get('total_tokens', 0):,} | "
                      f"小时使用: {stats['total_tokens']:,}/{self.hourly_limit:,}")

        except KeyboardInterrupt:
            print("\n✅ 监控已停止")

    def get_optimization_suggestions(self) -> List[str]:
        """基于使用模式提供优化建议"""
        suggestions = []

        day_stats = self.get_usage_stats('day')

        if day_stats['total_tokens'] > self.daily_limit * 0.8:
            suggestions.append("日Token使用接近上限，建议启用更激进的优化策略")

        if day_stats['operation_count'] > 1000 and day_stats['avg_per_operation'] > 100:
            suggestions.append("单次操作Token消耗较高，建议优化提示词模板")

        from collections import Counter
        ops = [u['operation'] for u in self.usage_history[-100:]]
        most_common = Counter(ops).most_common(1)

        if most_common and most_common[0][1] > 50:
            suggestions.append(f"'{most_common[0][0]}' 操作频繁，建议添加缓存机制")

        return suggestions

if __name__ == '__main__':
    monitor = IntelligentMonitor()

    for i in range(10):
        monitor.record_usage('test_op', 1000)

    print(json.dumps(monitor.get_usage_stats(), indent=2))
    print("\n优化建议:")
    for s in monitor.get_optimization_suggestions():
        print(f" - {s}")
