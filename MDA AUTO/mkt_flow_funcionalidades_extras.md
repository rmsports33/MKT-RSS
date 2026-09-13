# 🚀 MKT Flow 3.0 - Análise de Lacunas & Funcionalidades Extras

## Problema Central Identificado
O sistema atual é excelente em **geração de conteúdo**, mas não resolve problemas operacionais/gerenciais que afiliados multi-plataformas enfrentam diariamente:
- Falta rastreabilidade de cada link em cada plataforma
- Sem visão consolidada de ROI por plataforma/produto/programa
- Nenhuma automação de agendamento multi-plataforma
- Sem alertas sobre performance em tempo real
- Compliance fragmentado por tarefa, não por plataforma

---

## 🔴 CAMADA 1: GESTÃO DE IDENTIDADES & CREDENCIAIS

### Problema
Afiliados usam múltiplas contas em Instagram, Facebook, TikTok, LinkedIn, etc. Sistema atual não diferencia.

### Funcionalidade: **Vault de Plataformas**
```python
# /app/vault_manager.py (NOVA)

class PlatformVault:
    """Gerencia credenciais e identidades por plataforma"""

    def register_platform_identity(
        self,
        platform: str,  # "instagram", "tiktok", etc
        account_name: str,
        oauth_token: str,
        meta_data: Dict  # nicho, público-alvo, tema
    ) -> str:
        """Registra nova identidade com versionamento"""
        # Retorna identity_id único por plataforma

    def get_active_accounts(self, affiliate_id: str) -> List[Dict]:
        """Lista todas as contas ativas do afiliado"""

    def get_platform_limits(self, platform: str) -> Dict:
        """Retorna rate limits, restrições de conteúdo"""
        # Instagram: 5 posts/dia, vídeos até 60min
        # TikTok: uploads ilimitados
        # LinkedIn: 1 post/dia recomendado para empresa
```

### Dados Armazenados
```json
{
  "identity_id": "identity_insta_123",
  "platform": "instagram",
  "account_name": "@meu_nicho_tech",
  "affiliate_id": "user_456",
  "oauth_token": "ENCRYPTED",
  "profile_theme": "tech_gadgets",
  "target_audience": "homens 25-40",
  "posting_frequency": "3x/semana",
  "rate_limits": {
    "max_posts_per_day": 5,
    "max_video_length_seconds": 60,
    "average_posting_interval_hours": 8
  },
  "performance_baseline": {
    "avg_engagement_rate": 0.045,
    "avg_reach": 1200,
    "best_posting_time": "20:00"
  },
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## 🔴 CAMADA 2: RASTREAMENTO INTELIGENTE DE LINKS

### Problema
"Não sei qual link em qual plataforma gerou cada conversão. Shopee diz que foram 47 cliques, mas onde eles vieram?"

### Funcionalidade: **Link Intelligence Hub**
```python
# /app/link_tracker.py (NOVA)

class LinkTrackerHub:
    """Sistema de rastreamento multi-nível de links"""

    def generate_smart_link(
        self,
        product_id: str,
        affiliate_program: str,  # "mercadolivre", "shopee"
        platform_identity_id: str,  # qual conta Instagram?
        content_type: str,  # "post", "story", "reels", "bio"
        campaign_id: str,  # agrupa múltiplos links
        utm_custom: Dict = None
    ) -> SmartLink:
        """Cria link rastreável com metadata embutida"""

        # Gera link como:
        # https://bit.ly/mkt_xyz_[platform]_[account]_[product]_[timestamp]
        # Com redirecionamento que injeta pixels de rastreamento

    def track_link_performance(self, smart_link_id: str) -> Dict:
        """Retorna performance em tempo real"""
        # {
        #   "clicks": 42,
        #   "conversions": 8,
        #   "revenue": 1250.50,
        #   "ctr": 0.19,
        #   "traffic_sources": {"direct": 10, "referral": 32},
        #   "devices": {"mobile": 35, "desktop": 7},
        #   "last_update": "2024-01-15T14:32:00Z"
        # }

    def detect_link_conflicts(self, product_id: str) -> List[str]:
        """Identifica links duplicados/conflitantes"""
        # Problema comum: mesmo produto em 3 plataformas,
        # mas apenas 1 recebe traffic. Sugere consolidar.
```

### Features Extras
- **Geo-tracking**: Sabe que clicks vindos de São Paulo convertem 3x mais
- **Device tracking**: Mobile vs Desktop tem padrões diferentes por plataforma
- **Fraud detection**: Detecta click farms, bots
- **Decay analysis**: Qual plataforma gera conversão mais rápida?

---

## 🔴 CAMADA 3: AGENDAMENTO MULTI-PLATAFORMA COM CALENDÁRIO

### Problema
"Preciso publicar conteúdo em Instagram, TikTok, Pinterest e LinkedIn em horários diferentes. Fazer na mão é caótico."

### Funcionalidade: **Intelligent Publisher Scheduler**
```python
# /app/scheduler_v2.py (EVOLUÇÃO DO EXISTENTE)

class MultiPlatformScheduler:
    """Agendamento inteligente com otimização automática"""

    def schedule_content_campaign(
        self,
        content_id: str,
        platform_identities: List[str],  # múltiplas contas
        scheduling_strategy: str = "optimal"  # auto, manual, timezone_based
    ) -> CampaignSchedule:
        """Agenda conteúdo em múltiplas plataformas"""

        # Estratégia "optimal":
        # - Instagram: melhor horário para seu público (aprende com histórico)
        # - TikTok: 2 horas depois (aproveita impulso do Instagram)
        # - Pinterest: próximo dia (Pinterest tem ciclo mais longo)
        # - LinkedIn: 09:00 AM (padrão B2B)

    def get_calendar_view(self, start_date: str, end_date: str) -> Dict:
        """Retorna calendário consolidado de posts"""
        # {
        #   "2024-01-20": [
        #     {"time": "14:00", "platform": "instagram", "content": "...", "status": "scheduled"},
        #     {"time": "16:00", "platform": "tiktok", "content": "...", "status": "scheduled"}
        #   ],
        #   "capacity_warnings": ["TikTok: 3 posts em 2 horas (limite)"]
        # }

    def auto_reschedule_failed(self, post_id: str, reason: str) -> Dict:
        """Reagenda automaticamente se falha"""
        # Se Instagram falhar por copyright, reajusta e resubmete
```

### Dados Armazenados
```json
{
  "schedule_id": "sched_abc123",
  "content_id": "content_xyz",
  "campaign_id": "camp_001",
  "scheduling_plan": [
    {
      "platform": "instagram",
      "identity_id": "identity_insta_123",
      "scheduled_time": "2024-01-20T14:30:00Z",
      "estimated_reach": 1200,
      "estimated_engagement_rate": 0.045,
      "priority": 1
    },
    {
      "platform": "tiktok",
      "identity_id": "identity_tiktok_456",
      "scheduled_time": "2024-01-20T16:30:00Z",
      "estimated_reach": 3500,
      "estimated_engagement_rate": 0.12,
      "priority": 2
    }
  ],
  "auto_retry_config": {
    "max_attempts": 3,
    "backoff_minutes": [5, 15, 60]
  },
  "status": "scheduled"
}
```

---

## 🔴 CAMADA 4: DASHBOARD DE ROI CONSOLIDADO

### Problema
"Vendo dados no Mercado Livre, Shopee, Google Analytics, Facebook Ads Manager... Como saber meu retorno real?"

### Funcionalidade: **Unified ROI Dashboard**
```python
# /app/roi_consolidator.py (NOVA)

class UnifiedROIDashboard:
    """Consolida dados de múltiplas fontes de revenue"""

    def get_consolidated_metrics(
        self,
        date_range: Tuple[str, str],
        group_by: str = "platform"  # platform, product, program, identity
    ) -> Dict:
        """Retorna ROI consolidado"""

        # Exemplo: group_by="platform"
        # {
        #   "instagram": {
        #     "revenue": 5420.00,
        #     "conversions": 12,
        #     "clicks": 342,
        #     "spent": 0,  # links orgânicos
        #     "roi": "Infinito (orgânico)",
        #     "avg_order_value": 451.67,
        #     "top_product": "Smartwatch (8 vendas)"
        #   },
        #   "facebook_ads": {
        #     "revenue": 8200.00,
        #     "conversions": 18,
        #     "clicks": 890,
        #     "spent": 1200.00,  # ads
        #     "roi": 5.83,
        #     "ctr": 0.0202,
        #     "cpc": 1.35
        #   }
        # }

    def get_product_performance_matrix(self) -> DataFrame:
        """Matriz produto x plataforma"""
        #           Instagram  TikTok  Pinterest  LinkedIn
        # Produto1     $450      $0       $120      $300
        # Produto2     $0       $800      $0        $0
        # Produto3     $220     $340     $580      $0

    def detect_arbitrage_opportunities(self) -> List[Dict]:
        """Encontra desequilíbrios lucrativos"""
        # [
        #   {
        #     "insight": "Smartwatch em TikTok: 2.3x ROI vs Pinterest",
        #     "recommendation": "Aumentar budget TikTok em 50%",
        #     "potential_extra_revenue": 1200
        #   }
        # ]

    def forecast_revenue(self, days_ahead: int = 30) -> Dict:
        """Projeção baseada em histórico"""
        # Usa sazonalidade, tendências, volume de conteúdo planejado
```

### Dashboard Visualmente
```
┌─────────────────────────────────────────────────┐
│  MINHA AFILIAÇÃO - Últimos 30 dias             │
├─────────────────────────────────────────────────┤
│ Revenue Total: R$ 13.620,00  ↑12% vs mês ant. │
│ Conversões: 30  |  Ticket Médio: R$ 454,00     │
│ ROI Geral: 6.2x  |  CPA: R$ 454,00             │
├─────────────────────────────────────────────────┤
│ POR PLATAFORMA                                  │
├──────────────┬─────────┬───────┬────────────────┤
│ Plataforma   │ Revenue │ Conv. │ ROI            │
├──────────────┼─────────┼───────┼────────────────┤
│ 📱 Instagram │ R$5.4k  │ 12    │ ∞ (orgânico)   │
│ 🎵 TikTok    │ R$3.8k  │ 8     │ ∞ (orgânico)   │
│ 💰 F.Ads     │ R$2.8k  │ 7     │ 4.7x (R$600)   │
│ 📌 Pinterest │ R$1.6k  │ 3     │ ∞ (orgânico)   │
└──────────────┴─────────┴───────┴────────────────┘
```

---

## 🔴 CAMADA 5: COMPLIANCE AUTOMÁTICO AVANÇADO

### Problema
"Shopee bloqueou meu link. Mercado Livre reclamou de descrição enganosa. Como saber o quê exatamente violou?"

### Funcionalidade: **Policy Engine Amplificado**
```python
# /app/advanced_compliance.py (EVOLUÇÃO DO EXISTENTE)

class AdvancedComplianceEngine:
    """Validação multi-programa com sugestões de correção"""

    def validate_content_by_program(
        self,
        content: str,
        product_id: str,
        target_program: str,  # "shopee", "mercadolivre", "amazon"
        platform: str,  # qual plataforma vai publicar?
    ) -> ComplianceReport:
        """Valida contra regras específicas do programa"""

        # Retorna:
        # {
        #   "status": "NEEDS_FIXING",
        #   "violations": [
        #     {
        #       "rule": "SHOPEE_PRICE_CLAIM",
        #       "severity": "HIGH",
        #       "message": "Você afirma 'maior desconto'? Shopee exige comprovação.",
        #       "problematic_text": "MAIOR DESCONTO DA INTERNET",
        #       "fix_suggestion": "MELHOR PREÇO ENTRE MARCAS CONCORRENTES"
        #     },
        #     {
        #       "rule": "MERCADOLIVRE_SHIPPING_CLAIM",
        #       "severity": "MEDIUM",
        #       "message": "Fretis grátis prometido, mas produto custa R$50. ML aceita até R$150.",
        #       "fix_suggestion": "Aumentar preço ou remover promessa de frete"
        #     }
        #   ],
        #   "compliant_version": "Conteúdo corrigido aqui..."
        # }

    def check_platform_restrictions(self, platform: str, program: str):
        """Verifica restrições combinadas"""
        # Ex: Instagram + Shopee = sem links diretos, apenas bio
        # TikTok + Mercado Livre = link direto OK, mas com disclaimer

    def monitor_for_policy_changes(self):
        """Sistema de monitoring contínuo"""
        # Verifica mudanças nas políticas de Shopee/ML/Amazon
        # Emite alertas se afeta conteúdo já publicado
```

### Exemplo de Violação & Sugestão
```json
{
  "original_content": "INCRÍVEL! Fone Bluetooth JBL com 80% de desconto - ÚLTIMO ESTOQUE",
  "violations": [
    {
      "type": "MISLEADING_URGENCY",
      "program": "shopee",
      "rule_link": "https://shopee.com.br/policies/scarcity"
    }
  ],
  "suggested_fix": "Fone Bluetooth JBL com desconto especial - Aproveite enquanto durar",
  "confidence": 0.92
}
```

---

## 🔴 CAMADA 6: ANÁLISE COMPETITIVA & TREND DETECTION

### Problema
"Qual concorrente meu está ganhando? Que produto está bombando no TikTok que eu não explorei ainda?"

### Funcionalidade: **Competitive Intelligence Module**
```python
# /app/competitor_intel.py (NOVA)

class CompetitorIntel:
    """Monitora concorrentes e identifica oportunidades"""

    def monitor_competitors(
        self,
        competitor_platforms: List[str],  # URLs/contas
        category: str,  # "eletrônicos", "moda", etc
        frequency: str = "daily"
    ) -> Dict:
        """Monitora conteúdo de concorrentes"""
        # {
        #   "top_performing_content": [
        #     {
        #       "competitor": "@competitor_name",
        #       "content": "Unboxing Fone XYZ",
        #       "engagements": 4200,
        #       "engagement_rate": 0.087,
        #       "timestamp": "2024-01-18T14:30:00Z",
        #       "products_mentioned": ["Fone XYZ", "Cabo USB-C"]
        #     }
        #   ],
        #   "trend_alert": {
        #     "trend": "Unboxing videos",
        #     "velocity": "rising",
        #     "platforms": ["tiktok", "instagram_reels"],
        #     "recommendation": "Crie 2-3 unboxings por semana"
        #   }
        # }

    def identify_content_gaps(self) -> List[Dict]:
        """Encontra oportunidades não exploradas"""
        # [
        #   {
        #     "gap": "Nenhum concorrente faz tutorial de 'Smart TV + Soundbar'",
        #     "opportunity_score": 8.5,
        #     "estimated_potential": "2k+ views"
        #   }
        # ]

    def trending_products_by_platform(self, days: int = 7) -> Dict:
        """Produtos em trending"""
        # {
        #   "tiktok": {
        #     "trending": ["Smartwatch", "Fone wireless", "Webcam"],
        #     "growth_rate": ["+45%", "+32%", "+28%"]
        #   },
        #   "instagram": {
        #     "trending": ["iPhone cases", "Pop-its"],
        #     "growth_rate": ["+22%", "+18%"]
        #   }
        # }
```

---

## 🔴 CAMADA 7: SISTEMA DE ALERTAS INTELIGENTE

### Problema
"Acordei e meu link tá bloqueado. Não sabia. Perdi vendas o dia todo."

### Funcionalidade: **Smart Alert System**
```python
# /app/alert_manager.py (NOVA)

class SmartAlertManager:
    """Alertas prioritários em tempo real"""

    def setup_alerts(self, affiliate_id: str) -> None:
        """Configura alertas automáticos"""

    # Tipos de alerta:
    ALERT_TYPES = {
        "CRITICAL": [
            "link_blocked",  # Link foi desativado
            "account_flagged",  # Conta sinalizada
            "policy_violation",  # Violação detectada
            "revenue_anomaly"  # Revenue caiu 50% vs baseline
        ],
        "HIGH": [
            "performance_drop",  # CTR caiu 30%
            "competitor_surge",  # Concorrente superou você
            "trending_opportunity",  # Trend detectado relevante pro seu nicho
            "rate_limit_warning"  # Próximo de limite de posts
        ],
        "MEDIUM": [
            "slow_posting_day",  # Nenhum post nos últimos 6h
            "engagement_decline",  # Engagement caiu 20%
            "new_policy_announcement"  # Shopee/ML mudou regras
        ]
    }

    def create_alert_rule(
        self,
        alert_type: str,
        threshold: float,
        notification_channels: List[str]  # "telegram", "email", "push"
    ) -> str:
        """Cria regra de alerta"""
```

### Exemplo: Alert em Tempo Real
```
🚨 CRÍTICO - 14:32
Link bloqueado: mercadolivre.com/item/xyz
Razão: Imagem com marca concorrente detectada
Impacto estimado: R$450/dia (baseado em histórico)
✅ AÇÃO RÁPIDA: Editar conteúdo + Reativar (2min)
```

---

## 🔴 CAMADA 8: SISTEMA DE RELATÓRIOS INTELIGENTES

### Problema
"Cliente/programa pediu relatório. Montar manualmente é demora. E sempre falta algo."

### Funcionalidade: **Smart Report Generator**
```python
# /app/report_generator_v2.py (EVOLUÇÃO DO EXISTENTE)

class SmartReportGenerator:
    """Gera relatórios customizados automaticamente"""

    def generate_executive_summary(self, date_range: Tuple[str, str]) -> str:
        """Resumo executivo em 1 página"""
        # Markdown com:
        # - Highlights: revenue total, principais conversores
        # - Trends: o que subiu/desceu
        # - Recomendações: próximas ações

    def generate_program_report(
        self,
        program: str,  # "shopee", "mercadolivre"
        format: str = "pdf"
    ) -> bytes:
        """Relatório específico para programa"""
        # Inclui:
        # - Performance detalhada
        # - Compliance status
        # - Sugestões de melhoria
        # - Comparativo vs afiliados similares

    def generate_scheduled_reports(
        self,
        frequency: str,  # "daily", "weekly", "monthly"
        recipients: List[str],
        report_type: str  # "performance", "compliance", "roi"
    ) -> None:
        """Agenda envio automático"""
```

---

## 🔴 CAMADA 9: PORTFOLIO MANAGEMENT

### Problema
"Tenho 50 produtos. Qual devo focar? Qual tá morto e deveria parar?"

### Funcionalidade: **Smart Portfolio Manager**
```python
# /app/portfolio_manager.py (NOVA)

class PortfolioManager:
    """Análise dinâmica de portfolio de produtos"""

    def analyze_portfolio(self) -> PortfolioAnalysis:
        """Classifica produtos por performance"""

        # Segmentação automática:
        # "STARS" (alto potencial):
        #   - Fone JBL: R$1.2k/mês, 8% growth, tendência subindo
        #   - Smartwatch: R$800/mês, 12% growth
        #
        # "CASH COWS" (estável):
        #   - iPhone case: R$450/mês, 0% growth (maduro)
        #
        # "QUESTION MARKS" (incerto):
        #   - Webcam Logitech: R$120/mês, -15% growth, mas tendência subindo
        #
        # "DOGS" (parar):
        #   - Hub USB: R$30/mês, -20% growth, tendência descendo

    def get_portfolio_recommendations(self) -> List[Dict]:
        """Recomendações de alocação"""
        # [
        #   {
        #     "action": "INCREASE",
        #     "product": "Smartwatch",
        #     "reason": "Trending + high ROI",
        #     "suggested_allocation": "aumentar 40% do budget"
        #   },
        #   {
        #     "action": "DECREASE",
        #     "product": "Hub USB",
        #     "reason": "Declining trend",
        #     "suggested_action": "Remover ou repositionar"
        #   }
        # ]
```

---

## 🔴 CAMADA 10: INTEGRAÇÃO COM FERRAMENTAS DE TERCEIROS

### Problema
"Uso Google Analytics, Stripe, Canva, etc. Tudo desconectado."

### Funcionalidade: **Universal Integration Hub**
```python
# /app/integrations/ (NOVA)

class IntegrationHub:
    """Conecta com ecossistema de afiliado"""

    SUPPORTED_INTEGRATIONS = [
        # Analytics
        ("google_analytics", "Importa dados de conversão"),
        ("facebook_pixel", "Rastreia eventos"),

        # Payment
        ("stripe", "Sincroniza pagamentos recebidos"),
        ("paypal", "Sincroniza comissões"),

        # Design
        ("canva", "API para gerar variações automáticas"),
        ("figma", "Importa templates"),

        # Content
        ("hootsuite", "Publica em múltiplas plataformas"),
        ("buffer", "Agendamento alternativo"),

        # Email
        ("mailchimp", "Dispara newsletter com trending products"),
        ("sendpulse", "SMS com alertas"),

        # CRM
        ("notion", "Sincroniza leads/contatos"),
    ]

    def sync_with_platform(self, platform: str, config: Dict) -> bool:
        """Conecta e sincroniza dados"""
```

---

## 📊 MATRIZ DE IMPACTO (Priorização)

| Funcionalidade | Impacto | Dificuldade | ROI | Prioridade |
|---|---|---|---|---|
| Vault de Plataformas | Alto | Baixa | 8/10 | 🔴 P1 |
| Link Intelligence | Crítico | Média | 9/10 | 🔴 P1 |
| Multi-Platform Scheduler | Alto | Média | 8/10 | 🔴 P1 |
| Unified ROI Dashboard | Crítico | Média | 9/10 | 🔴 P1 |
| Advanced Compliance | Alto | Alta | 7/10 | 🟡 P2 |
| Competitor Intel | Médio | Alta | 6/10 | 🟡 P2 |
| Smart Alerts | Alto | Baixa | 8/10 | 🔴 P1 |
| Report Generator | Médio | Baixa | 7/10 | 🟡 P2 |
| Portfolio Manager | Médio | Média | 7/10 | 🟡 P2 |
| Integration Hub | Médio | Alta | 6/10 | 🟡 P3 |

---

## 🎯 ROADMAP SUGERIDO (Implementação)

### Fase 1 (Semanas 1-4) - MVP Core
- ✅ Vault de Plataformas
- ✅ Link Intelligence (versão básica)
- ✅ Smart Alerts

### Fase 2 (Semanas 5-8) - Analytics
- ✅ Unified ROI Dashboard
- ✅ Portfolio Manager
- ✅ Report Generator

### Fase 3 (Semanas 9-12) - Automação
- ✅ Multi-Platform Scheduler V2
- ✅ Advanced Compliance
- ✅ Integration Hub

### Fase 4 (Semanas 13+) - Intelligence
- ✅ Competitor Intel
- ✅ Trend Detection
- ✅ Content Gap Analysis

---

## 💾 ESTRUTURA DE BANCO DE DADOS NECESSÁRIA

```sql
-- Tabelas adicionais requeridas

CREATE TABLE platform_identities (
    id UUID PRIMARY KEY,
    affiliate_id UUID NOT NULL,
    platform VARCHAR(50),
    account_name VARCHAR(255),
    oauth_token ENCRYPTED,
    metadata JSONB,
    performance_baseline JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE smart_links (
    id UUID PRIMARY KEY,
    original_url TEXT,
    short_url VARCHAR(100) UNIQUE,
    platform_identity_id UUID,
    product_id VARCHAR(255),
    program VARCHAR(100),
    content_type VARCHAR(50),
    campaign_id UUID,
    created_at TIMESTAMP,
    INDEX (campaign_id, platform_identity_id)
);

CREATE TABLE link_performance (
    smart_link_id UUID PRIMARY KEY,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    revenue DECIMAL(10,2),
    traffic_sources JSONB,
    device_breakdown JSONB,
    last_updated TIMESTAMP,
    FOREIGN KEY (smart_link_id) REFERENCES smart_links(id)
);

CREATE TABLE platform_schedules (
    id UUID PRIMARY KEY,
    campaign_id UUID,
    content_id VARCHAR(255),
    scheduled_time TIMESTAMP,
    platform VARCHAR(50),
    identity_id UUID,
    status VARCHAR(20),
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP
);

CREATE TABLE compliance_violations (
    id UUID PRIMARY KEY,
    content_id VARCHAR(255),
    program VARCHAR(100),
    rule_violated VARCHAR(255),
    severity VARCHAR(20),
    message TEXT,
    suggested_fix TEXT,
    created_at TIMESTAMP
);

CREATE TABLE competitor_monitoring (
    id UUID PRIMARY KEY,
    competitor_handle VARCHAR(255),
    platform VARCHAR(50),
    content_hash VARCHAR(64) UNIQUE,
    engagement_metrics JSONB,
    products_mentioned JSONB,
    first_seen TIMESTAMP,
    last_checked TIMESTAMP
);

CREATE TABLE portfolio_analysis (
    id UUID PRIMARY KEY,
    affiliate_id UUID,
    product_id VARCHAR(255),
    category VARCHAR(50),
    monthly_revenue DECIMAL(10,2),
    growth_rate DECIMAL(5,2),
    classification VARCHAR(20),  -- STAR, CASH_COW, QUESTION_MARK, DOG
    last_analyzed TIMESTAMP
);

CREATE TABLE alert_rules (
    id UUID PRIMARY KEY,
    affiliate_id UUID,
    alert_type VARCHAR(50),
    threshold DECIMAL(10,2),
    notification_channels JSONB,
    enabled BOOLEAN,
    created_at TIMESTAMP
);

CREATE TABLE alert_history (
    id UUID PRIMARY KEY,
    rule_id UUID,
    triggered_at TIMESTAMP,
    values JSONB,
    action_taken VARCHAR(255),
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
);
```

---

## 🔧 EXEMPLO DE IMPLEMENTAÇÃO: Link Intelligence

```python
# /app/link_tracker.py (Exemplo completo)

import hashlib
import uuid
from datetime import datetime
from typing import Dict, List
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SmartLink(Base):
    __tablename__ = 'smart_links'

    id = Column(String, primary_key=True)
    short_url = Column(String, unique=True)
    platform_identity_id = Column(String)
    product_id = Column(String)
    affiliate_program = Column(String)
    content_type = Column(String)
    campaign_id = Column(String)
    utm_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class LinkPerformance(Base):
    __tablename__ = 'link_performance'

    smart_link_id = Column(String, primary_key=True)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Integer, default=0)  # em centavos
    ctr = Column(Integer, default=0)  # em centésimos
    traffic_sources = Column(JSON)
    device_breakdown = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)

class LinkTrackerHub:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

    def generate_smart_link(
        self,
        product_id: str,
        affiliate_program: str,
        platform_identity_id: str,
        content_type: str,
        campaign_id: str,
        utm_custom: Dict = None
    ) -> Dict:
        """Gera link inteligente rastreável"""

        link_id = str(uuid.uuid4())

        # Build URL parameter string
        utm_params = {
            "utm_source": self._get_platform_name(platform_identity_id),
            "utm_medium": "social",
            "utm_campaign": campaign_id,
            "utm_content": link_id,
            "utm_term": "mkt_flow",
            "mkt_flow_id": link_id,  # nosso rastreamento próprio
            "content_type": content_type,
            "product_id": product_id
        }

        if utm_custom:
            utm_params.update(utm_custom)

        # Shortening (stub - seria integrado com bit.ly ou similar)
        short_url = f"https://mktflow.io/{link_id[:8]}"

        # Save to DB
        smart_link = SmartLink(
            id=link_id,
            short_url=short_url,
            platform_identity_id=platform_identity_id,
            product_id=product_id,
            affiliate_program=affiliate_program,
            content_type=content_type,
            campaign_id=campaign_id,
            utm_params=utm_params
        )

        # Initialize performance tracking
        performance = LinkPerformance(
            smart_link_id=link_id,
            traffic_sources={},
            device_breakdown={"mobile": 0, "desktop": 0}
        )

        return {
            "smart_link_id": link_id,
            "short_url": short_url,
            "full_tracking_url": f"{short_url}?{self._dict_to_query(utm_params)}",
            "created_at": datetime.utcnow().isoformat(),
            "platform": self._get_platform_name(platform_identity_id),
            "affiliate_program": affiliate_program
        }

    def track_link_performance(self, smart_link_id: str) -> Dict:
        """Retorna performance em tempo real"""
        # Buscar dados de múltiplas fontes:
        # 1. Webhooks do Shopee/Mercado Livre
        # 2. Pixels de rastreamento
        # 3. APIs de analytics

        return {
            "smart_link_id": smart_link_id,
            "clicks": 42,
            "conversions": 8,
            "revenue": 1250.50,
            "ctr": 0.19,
            "conversion_rate": 0.19,
            "average_order_value": 156.31,
            "traffic_sources": {
                "direct": 10,
                "referral": 32
            },
            "devices": {
                "mobile": 35,
                "desktop": 7
            },
            "geographic": {
                "SP": 25,
                "RJ": 12,
                "MG": 5
            },
            "last_update": datetime.utcnow().isoformat()
        }

    def _get_platform_name(self, platform_identity_id: str) -> str:
        # Buscar nome da plataforma no banco
        return "instagram"  # stub

    def _dict_to_query(self, params: Dict) -> str:
        return "&".join([f"{k}={v}" for k, v in params.items()])
```

---

## ✨ DIFERENCIAIS COMPETITIVOS

Com essas funcionalidades, MKT Flow 3.0 se tornaria:

1. **Único em consolidação**: Dashboard consolidado que nenhum concorrente oferece
2. **Proativo em alertas**: Detecta problemas antes de impactar revenue
3. **Automatizado**: Reduz 70% do trabalho manual de afiliados
4. **Inteligente**: Recomendações baseadas em dados (não suposições)
5. **Escalável**: Suporta 50+ contas simultâneas sem confusão
6. **Compliance-first**: Evita bloqueios e punições

---

## 📝 NOTAS PARA DESENVOLVIMENTO

- **Prioridade**: P1 funcionalidades geram 80% do valor
- **Tech stack**: Manter Python/FastAPI/Redis + adicionar TimescaleDB para time-series
- **Security**: Links encriptados, tokens com TTL curto, auditoria completa
- **Performance**: Cache agressivo para dashboards, processamento assíncrono de analytics
