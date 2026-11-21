from pathlib import Path
from decimal import Decimal
import os
ROOT=Path(__file__).resolve().parent.parent
DATA_DIR=Path(os.environ.get("DATA_DIR", "/tmp/transitcap"))
TITLE='公交刷卡换乘优惠与日封顶回算'
SHORT='transitcap'
COLUMNS=['event_id', 'card', 'route', 'event_time', 'result', 'reported', 'ticket_type', 'note']
# 票种裁决：权益按普通票价基数，应收与补贴按票种实付基数（见 docs/RULING.md）
TICKET_TYPES={'普通':Decimal('1.00'),'学生':Decimal('0.50'),'老年':Decimal('0.20')}
MODULES=[('taps', '刷卡采信'), ('routes', '线路换乘'), ('fares', '票价版本'), ('journeys', '行程配对'), ('discounts', '优惠回算'), ('clearing', '清分对账'), ('settlement', '日结归档')]
RULE_VERSION="2026.11.21-r2"
