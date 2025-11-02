"""
DRDO Equipment Maintenance Dashboard using Streamlit.

Provides real-time monitoring of equipment health and maintenance alerts.
Minimal essential features for production readiness.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import logging

from .api_client import AlertServiceClient, MLServiceClient
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"dashboard","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="DRDO Equipment Monitor",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════

st.title("🛡️ DRDO Equipment Maintenance Dashboard")
st.markdown("**Real-time predictive maintenance monitoring for defense equipment**")
st.divider()

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR - REFRESH CONTROL ONLY
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    
    st.markdown("### Refresh Data")
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Cache clear button
    if st.button("🗑️ Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared!")
        st.rerun()
    
    st.divider()
    
    # Service information
    st.markdown("### Service Info")
    st.caption(f"**Service:** {settings.SERVICE_NAME}")
    st.caption(f"**Version:** {settings.SERVICE_VERSION}")
    st.caption(f"**Port:** {settings.PORT}")
    
    st.divider()
    
    # Timestamp
    st.caption(f"⏰ Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    st.caption(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")

# ═══════════════════════════════════════════════════════════════════
# DATA FETCHING (CACHED)
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=settings.CACHE_TTL)
def fetch_alerts():
    """
    Fetch active alerts from alert service.
    
    Returns:
        DataFrame with alert data or empty DataFrame on error
    """
    logger.info("Fetching alerts from API")
    
    client = AlertServiceClient()
    alerts = client.get_active_alerts()
    
    if not alerts:
        logger.warning("No alerts received from API")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(alerts)
    
    # Ensure required columns exist with defaults
    required_cols = {
        'id': '',
        'equipment_id': 'UNKNOWN',
        'severity': 'UNKNOWN',
        'failure_probability': 0.0,
        'days_until_failure': 0,
        'created_at': '',
        'health_score': 0.0,
        'recommended_action': ''
    }
    
    for col, default_value in required_cols.items():
        if col not in df.columns:
            df[col] = default_value
    
    logger.info(f"Loaded {len(df)} alerts into DataFrame")
    return df

@st.cache_data(ttl=60)
def check_service_health():
    """
    Check health of all microservices.
    
    Returns:
        Dictionary with service health status
    """
    alert_client = AlertServiceClient()
    ml_client = MLServiceClient()
    
    return {
        'alert_service': alert_client.health_check(),
        'ml_service': ml_client.health_check()
    }

# ═══════════════════════════════════════════════════════════════════
# FETCH DATA
# ═══════════════════════════════════════════════════════════════════

with st.spinner("Loading dashboard data..."):
    alerts_df = fetch_alerts()
    service_health = check_service_health()

# ═══════════════════════════════════════════════════════════════════
# METRICS ROW (4 KEY STATISTICS)
# ═══════════════════════════════════════════════════════════════════

if not alerts_df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_alerts = len(alerts_df)
        st.metric(
            label="🔔 Total Alerts",
            value=total_alerts,
            help="Total number of active alerts"
        )
    
    with col2:
        critical_count = len(alerts_df[alerts_df['severity'] == 'CRITICAL'])
        st.metric(
            label="🔴 Critical",
            value=critical_count,
            delta=f"{(critical_count/total_alerts*100):.0f}%" if total_alerts > 0 else "0%",
            delta_color="inverse",
            help="Critical severity alerts requiring immediate attention"
        )
    
    with col3:
        high_count = len(alerts_df[alerts_df['severity'] == 'HIGH'])
        st.metric(
            label="🟠 High Priority",
            value=high_count,
            delta=f"{(high_count/total_alerts*100):.0f}%" if total_alerts > 0 else "0%",
            delta_color="inverse",
            help="High priority alerts"
        )
    
    with col4:
        avg_failure_prob = alerts_df['failure_probability'].mean() * 100
        st.metric(
            label="📊 Avg Failure Risk",
            value=f"{avg_failure_prob:.1f}%",
            help="Average failure probability across all equipment"
        )
    
    st.divider()

else:
    st.info("✅ **No active alerts.** All equipment operating normally.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# VISUALIZATION ROW (3 CHARTS)
# ═══════════════════════════════════════════════════════════════════

st.subheader("📊 Alert Analytics")

# Define severity colors
severity_colors = {
    'CRITICAL': '#FF4B4B',  # Red
    'HIGH': '#FFA500',      # Orange
    'MEDIUM': '#FFD700',    # Gold
    'LOW': '#90EE90'        # Light Green
}

col1, col2, col3 = st.columns(3)

# ─────────────────────────────────────────────────────────────────
# CHART 1: Severity Distribution (Pie Chart)
# ─────────────────────────────────────────────────────────────────

with col1:
    st.markdown("##### Severity Distribution")
    
    severity_counts = alerts_df['severity'].value_counts()
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=severity_counts.index,
        values=severity_counts.values,
        marker=dict(
            colors=[severity_colors.get(s, '#888888') for s in severity_counts.index]
        ),
        hole=0.4,
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig_pie.update_layout(
        height=350,
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

# ─────────────────────────────────────────────────────────────────
# CHART 2: Equipment Failure Probability (Bar Chart)
# ─────────────────────────────────────────────────────────────────

with col2:
    st.markdown("##### Top Equipment by Risk")
    
    # Get top 10 equipment by failure probability
    top_equipment = alerts_df.nlargest(10, 'failure_probability')[
        ['equipment_id', 'failure_probability', 'severity']
    ].copy()
    
    # Create bar chart
    fig_bar = go.Figure(data=[go.Bar(
        x=top_equipment['equipment_id'],
        y=top_equipment['failure_probability'] * 100,
        marker=dict(
            color=[severity_colors.get(s, '#888888') for s in top_equipment['severity']],
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=top_equipment['failure_probability'].apply(lambda x: f'{x*100:.0f}%'),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>'
    )])
    
    fig_bar.update_layout(
        xaxis_title="Equipment ID",
        yaxis_title="Failure Probability (%)",
        height=350,
        margin=dict(l=20, r=20, t=20, b=80),
        showlegend=False,
        yaxis=dict(range=[0, 100])
    )
    
    fig_bar.update_xaxes(tickangle=-45)
    
    st.plotly_chart(fig_bar, use_container_width=True)

# ─────────────────────────────────────────────────────────────────
# CHART 3: Risk vs Time to Failure (Scatter Plot)
# ─────────────────────────────────────────────────────────────────

with col3:
    st.markdown("##### Risk vs Time to Failure")
    
    fig_scatter = px.scatter(
        alerts_df,
        x='days_until_failure',
        y='failure_probability',
        color='severity',
        hover_data={
            'equipment_id': True,
            'failure_probability': ':.2%',
            'days_until_failure': True,
            'severity': True
        },
        color_discrete_map=severity_colors,
        labels={
            'days_until_failure': 'Days Until Failure',
            'failure_probability': 'Failure Probability',
            'severity': 'Severity'
        }
    )
    
    fig_scatter.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    
    fig_scatter.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(tickformat='.0%')
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════
# ACTIVE ALERTS TABLE
# ═══════════════════════════════════════════════════════════════════

st.subheader("📋 Active Alerts")

# Format DataFrame for display
display_df = alerts_df.copy()

# Convert datetime if string
if 'created_at' in display_df.columns:
    try:
        display_df['created_at'] = pd.to_datetime(display_df['created_at'])
        display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        logger.warning(f"Could not parse created_at: {e}")

# Format failure probability as percentage
if 'failure_probability' in display_df.columns:
    display_df['failure_probability'] = display_df['failure_probability'].apply(
        lambda x: f'{x*100:.1f}%' if pd.notnull(x) else 'N/A'
    )

# Format health score
if 'health_score' in display_df.columns:
    display_df['health_score'] = display_df['health_score'].apply(
        lambda x: f'{x:.1f}' if pd.notnull(x) else 'N/A'
    )

# Select and rename columns for display
display_cols = ['equipment_id', 'severity', 'failure_probability', 
                'health_score', 'days_until_failure', 'created_at']

# Filter to existing columns
display_cols = [col for col in display_cols if col in display_df.columns]

display_df_final = display_df[display_cols].rename(columns={
    'equipment_id': 'Equipment ID',
    'severity': 'Severity',
    'failure_probability': 'Failure Risk',
    'health_score': 'Health Score',
    'days_until_failure': 'Days Until Failure',
    'created_at': 'Created At'
})

# Apply styling based on severity
def highlight_severity(row):
    """Apply row styling based on severity."""
    severity = row.get('Severity', '')
    if severity == 'CRITICAL':
        return ['background-color: rgba(255, 75, 75, 0.1)'] * len(row)
    elif severity == 'HIGH':
        return ['background-color: rgba(255, 165, 0, 0.1)'] * len(row)
    elif severity == 'MEDIUM':
        return ['background-color: rgba(255, 215, 0, 0.1)'] * len(row)
    else:
        return [''] * len(row)

# Display table with styling
st.dataframe(
    display_df_final.style.apply(highlight_severity, axis=1),
    use_container_width=True,
    height=400,
    hide_index=True
)

st.caption(f"📊 Showing **{len(alerts_df)}** active alerts")

st.divider()

# ═══════════════════════════════════════════════════════════════════
# FOOTER - SERVICE STATUS
# ═══════════════════════════════════════════════════════════════════

col1, col2, col3 = st.columns(3)

with col1:
    if service_health.get('alert_service', False):
        st.success("✅ Alert Service Connected")
    else:
        st.error("❌ Alert Service Disconnected")

with col2:
    if service_health.get('ml_service', False):
        st.success("✅ ML Service Connected")
    else:
        st.warning("⚠️ ML Service Unavailable")

with col3:
    st.info(f"📡 Updated: {datetime.now().strftime('%H:%M:%S')}")

# ═══════════════════════════════════════════════════════════════════
# DEBUG INFO (HIDDEN)
# ═══════════════════════════════════════════════════════════════════

with st.expander("🔧 Debug Information"):
    st.json({
        "total_alerts": len(alerts_df),
        "service_health": service_health,
        "cache_ttl": settings.CACHE_TTL,
        "alert_service_url": settings.ALERT_SERVICE_URL,
        "ml_service_url": settings.ML_SERVICE_URL
    })
