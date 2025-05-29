import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
import pandas as pd
import os
from datetime import datetime

API_BASE_URL = os.getenv('API_BASE_URL', 'http://api-server:8000')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

st.set_page_config(
    page_title="📊 Dimeo Retention Analytics",
    page_icon="🎬", 
    layout="wide"
)

class RetentionAnalyzer:
    def __init__(self):
        self.api_base = API_BASE_URL
        
    def get_videos(self) -> List[Dict]:
        """Retrieves the list of available videos"""
        try:
            response = requests.get(f"{self.api_base}/videos")
            if response.status_code == 200:
                return response.json()['videos']
            return []
        except Exception as e:
            st.error(f"Error retrieving videos: {e}")
            return []
    
    def get_retention_curve(self, video_id: str) -> Dict:
        """Retrieves the retention curve"""
        try:
            response = requests.get(f"{self.api_base}/video/{video_id}/retention_curve")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            st.error(f"Error retrieving retention curve: {e}")
            return {}
    
    def get_dropoffs(self, video_id: str, threshold: float = 10.0) -> Dict:
        """Retrieves significant dropoff points"""
        try:
            response = requests.get(
                f"{self.api_base}/video/{video_id}/significant_dropoffs?threshold_percentage={threshold}"
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            st.error(f"Error retrieving dropoffs: {e}")
            return {}
    
    def get_engagement_summary(self, video_id: str) -> Dict:
        """Retrieves engagement summary"""
        try:
            response = requests.get(f"{self.api_base}/video/{video_id}/engagement_summary")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            st.error(f"Error retrieving engagement summary: {e}")
            return {}

class DimeoAnalystAgent:
    def __init__(self):
        self.openai_client = None
        self.api_key_status = "not_configured"
        
        if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
            self.api_key_status = "not_configured"
            return
            
        if not OPENAI_API_KEY.startswith('sk-'):
            self.api_key_status = "invalid_format"
            return
        
        try:
            import openai
            
            openai.api_key = OPENAI_API_KEY.strip()
            
            response = openai.Model.list()
            self.api_key_status = "valid"
            self.openai_client = openai
            
        except ImportError:
            self.api_key_status = "library_missing"
        except Exception as e:
            self.api_key_status = f"connection_error: {str(e)}"
    
    def get_status_message(self) -> tuple:
        """Returns status message and color for UI"""
        if self.api_key_status == "valid":
            return "✅ Dimeo AI Analyst ready", "success"
        elif self.api_key_status == "not_configured":
            return "⚠️ No OpenAI API key configured", "warning"
        elif self.api_key_status == "invalid_format":
            return "❌ Invalid API key format (should start with 'sk-')", "error"
        elif self.api_key_status == "library_missing":
            return "❌ OpenAI library not installed", "error"
        else:
            return f"❌ Connection error: {self.api_key_status}", "error"
    
    def analyze_retention_data(self, video_id: str, retention_data: Dict, 
                             dropoffs_data: Dict, engagement_data: Dict) -> str:
        """Analyzes retention data as a Dimeo expert or demo mode"""
        
        # Use demo mode if OpenAI client is not available
        if not self.openai_client or self.api_key_status != "valid":
            return self._Dimeo_expert_demo_analysis(video_id, retention_data, dropoffs_data, engagement_data)
        
        prompt = self._create_Dimeo_analyst_prompt(video_id, retention_data, dropoffs_data, engagement_data)
        
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are Sarah Chen, a Senior Video Analytics Specialist at Dimeo with 8 years of experience. 
                        You work directly with content creators to optimize their video performance. Your expertise includes:
                        - Video retention optimization strategies
                        - Content creator psychology and viewer behavior
                        - A/B testing methodologies for video content  
                        - Industry benchmarks and best practices
                        
                        You speak in a professional but friendly tone, always providing specific, actionable advice based on data.
                        You reference industry standards and your experience working with thousands of creators on the Dimeo platform."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"❌ AI Analysis Error: {str(e)}"
            return error_msg + "\n\n" + self._Dimeo_expert_demo_analysis(video_id, retention_data, dropoffs_data, engagement_data)
    
    def _Dimeo_expert_demo_analysis(self, video_id: str, retention_data: Dict, dropoffs_data: Dict, engagement_data: Dict) -> str:
        """Demo analysis as a Dimeo expert for testing the interface"""
        
        total_viewers = retention_data.get('total_unique_viewers', 0)
        avg_watch_time = engagement_data.get('average_watch_time_sec', 0)
        dropoffs_count = len(dropoffs_data.get('drop_offs', []))
        data_points = retention_data.get('data_points', [])
        video_duration = max([dp['video_time_sec'] for dp in data_points]) if data_points else 1
        completion_rate = (avg_watch_time / video_duration * 100) if video_duration > 0 else 0
        
        # Get the biggest dropoffs for analysis
        biggest_dropoffs = sorted(dropoffs_data.get('drop_offs', []), 
                                key=lambda x: x['drop_off_percentage'], reverse=True)[:3]
        
        # Create dropoff analysis text
        dropoff_analysis = ""
        if biggest_dropoffs:
            dropoff_lines = []
            for dropoff in biggest_dropoffs:
                line = f"**⚠️ Second {dropoff['video_time_sec']}**: Lost {dropoff['drop_off_count']} viewers (-{dropoff['drop_off_percentage']:.1f}%)"
                dropoff_lines.append(line)
            dropoff_analysis = "\n".join(dropoff_lines)
        
        # Create specific recommendations for biggest dropoffs
        specific_recommendations = ""
        if biggest_dropoffs:
            rec_lines = []
            for dropoff in biggest_dropoffs[:2]:
                if dropoff['drop_off_percentage'] > 15:
                    rec = f"   - **Second {dropoff['video_time_sec']}**: Likely a pacing issue - try shortening this segment"
                else:
                    rec = f"   - **Second {dropoff['video_time_sec']}**: Consider adding a transition or preview here"
                rec_lines.append(rec)
            specific_recommendations = "\n".join(rec_lines)
        else:
            specific_recommendations = "   - Focus on maintaining the positive momentum you have"
        
        # Determine performance levels
        if total_viewers > 10:
            viewer_assessment = "That's a solid start!"
        else:
            viewer_assessment = "Building your audience takes time"
            
        if completion_rate > 25:
            completion_assessment = "Above average for most content!"
        elif completion_rate > 15:
            completion_assessment = "Room for improvement here"
        else:
            completion_assessment = "This needs immediate attention"
            
        if completion_rate > 25:
            performance_level = "🟢 **Above average** - you're doing something right!"
        elif completion_rate > 15:
            performance_level = "🟡 **Average range** - with optimization, you can improve"
        else:
            performance_level = "🔴 **Below average** - let's fix this together"
            
        if dropoffs_count > 0:
            dropoff_intro = f"I've identified **{dropoffs_count} significant viewer exit points**. Here are the most concerning:"
        else:
            dropoff_intro = "Great news! No major drop-offs detected. Your content flow is solid."
            
        if dropoffs_count > 10:
            assessment = "**Multiple drop-offs concern me.** "
        elif dropoffs_count > 5:
            assessment = "**Some strategic improvements needed.** "
        else:
            assessment = "**Good foundation to build on.** "
            
        if completion_rate < 30:
            main_cause = "1. **Hook isn't strong enough** - First 15 seconds are crucial"
        else:
            main_cause = "1. **Content pacing issues** - Some segments may drag"
            
        if dropoffs_count > 8:
            extra_cause = "4. **Content density** - Too much information too quickly"
        else:
            extra_cause = ""
            
        if completion_rate < 25:
            immediate_fix = "Redesign your opening 30 seconds"
            hook_advice = "Create a compelling hook that clearly states the value"
            pattern_advice = "Use pattern interrupt techniques I teach our creators"
        else:
            immediate_fix = "Analyze your strongest retention segments"
            hook_advice = "Identify what worked and replicate that formula"
            pattern_advice = "Consider A/B testing variations of successful moments"
            
        if dropoffs_count > 5:
            structure_advice = 'Add more "coming up" previews to maintain interest'
        else:
            structure_advice = "Your structure seems solid - minor tweaks only"
            
        if completion_rate < 30:
            strategic_improvement = "**A/B test different openings** with a small audience segment"
        else:
            strategic_improvement = "**Scale what's working** - apply successful elements to other videos"
            
        if avg_watch_time > 60:
            working_well = "Your content has substance - viewers who stay tend to watch longer segments"
        else:
            working_well = "You're attracting viewers, which means your topic/thumbnail combo works"
            
        if dropoffs_count > 0:
            next_opportunity = "Focus on retention optimization - small changes can yield big results"
        else:
            next_opportunity = "You're ready to scale - apply these learnings to more content"
        
        return f"""
# 📊 Dimeo Analytics Report by Sarah Chen
*Senior Video Analytics Specialist - Dimeo Creator Services*

---

## 🎯 Executive Summary

Hey there! I've analyzed your video **{video_id[:8]}...** and here's what the data tells us:

**Performance Overview:**
- 👥 **{total_viewers:,} unique viewers** - {viewer_assessment}
- ⏱️ **{avg_watch_time:.1f}s average view duration** 
- ✅ **{completion_rate:.1f}% completion rate** - {completion_assessment}

## 📈 Industry Context

Based on my work with **thousands of creators on Dimeo**, here's how you stack up:

- **Completion Rate Benchmark**: 20-30% is typical for educational content, 15-25% for entertainment
- **Your Performance**: {performance_level}

## 🚨 Critical Drop-off Analysis

{dropoff_intro}

{dropoff_analysis}

## 💡 My Professional Assessment

{assessment}

Based on patterns I see across our platform:

### Most Likely Causes:
{main_cause}
2. **Unclear value proposition** - Viewers don't know what they'll get
3. **Technical transitions** - Abrupt cuts or topic jumps
{extra_cause}

## 🚀 My Recommended Action Plan

Here's what I'd do if this were my video:

### Immediate Fixes (This Week):
1. **{immediate_fix}**
   - {hook_advice}
   - {pattern_advice}

2. **Address the biggest drop-off points:**
{specific_recommendations}

3. **Content Structure Review:**
   - {structure_advice}
   - Use the "tell them what you'll tell them" principle

### Strategic Improvements (Next 2 Weeks):
- {strategic_improvement}
- **Study your audience retention heatmap** for pattern recognition
- **Create content milestones** every 30-45 seconds to maintain engagement

## 📊 Success Indicators to Track

I recommend monitoring these metrics weekly:
- Target completion rate: {completion_rate + 10:.1f}% (achievable 10% improvement)
- Reduce major drop-offs to under 5 points
- Increase average view duration to {avg_watch_time + 30:.1f}s

## 🎬 Personal Note

I've worked with creators who started exactly where you are now and went on to build massive audiences. The data shows you have potential - we just need to optimize the viewer experience.

**What's working well:** {working_well}

**Next level opportunity:** {next_opportunity}

---

*📞 **Want to discuss this analysis?** Book a Creator Success session through your Dimeo dashboard*

*🤖 **Note**: This is a demo analysis. Connect your OpenAI API key for personalized insights from our AI-powered Dimeo analyst!*

### 🔑 Enable Full AI Analysis:
1. Get your API key: [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set `OPENAI_API_KEY` environment variable  
3. Restart the application for full Dimeo expert analysis

---
*Analysis by Sarah Chen, Senior Video Analytics Specialist*  
*Dimeo Creator Services Team*
"""
    
    def _create_Dimeo_analyst_prompt(self, video_id: str, retention_data: Dict, 
                                   dropoffs_data: Dict, engagement_data: Dict) -> str:
        """Creates the analysis prompt for the Dimeo expert"""
        
        # Extract key data
        total_viewers = retention_data.get('total_unique_viewers', 0)
        data_points = retention_data.get('data_points', [])
        dropoffs = dropoffs_data.get('drop_offs', [])
        avg_watch_time = engagement_data.get('average_watch_time_sec', 0)
        
        # Calculate total video duration
        video_duration = max([dp['video_time_sec'] for dp in data_points]) if data_points else 1
        completion_rate = (avg_watch_time / video_duration * 100)
        
        # Create retention data summary
        retention_summary = []
        for dp in data_points[:15]:  # More data points for AI
            retention_summary.append(f"T{dp['video_time_sec']}s: {dp['current_viewers']} viewers ({dp['retention_percentage']:.1f}%)")
        
        # Summary of significant dropoffs
        dropoff_summary = []
        for dropoff in dropoffs[:8]:  # Top 8 dropoffs
            dropoff_summary.append(f"T{dropoff['video_time_sec']}s: -{dropoff['drop_off_count']} viewers (-{dropoff['drop_off_percentage']:.1f}%)")
        
        prompt = f"""
I need your expert analysis of this video's retention performance for one of our Dimeo creators.

VIDEO ANALYTICS DATA:
- Video ID: {video_id}
- Total unique viewers: {total_viewers:,}
- Video duration: {video_duration}s  
- Average watch time: {avg_watch_time:.1f}s
- Completion rate: {completion_rate:.1f}%

RETENTION CURVE DATA:
{chr(10).join(retention_summary) if retention_summary else 'Limited retention data'}

SIGNIFICANT VIEWER DROP-OFFS:
{chr(10).join(dropoff_summary) if dropoff_summary else 'No major drop-offs detected'}

As a Dimeo expert, please provide:

1. **Industry Context**: How does this perform vs. typical Dimeo content in this completion rate range?

2. **Root Cause Analysis**: What are the most likely reasons for the drop-off patterns you see? Draw from your experience with similar creators.

3. **Specific Action Plan**: Give 3-4 concrete, implementable recommendations that you would give this creator in a one-on-one consultation.

4. **Success Metrics**: What specific targets should they aim for in the next 30 days?

5. **Encouragement & Next Steps**: End with motivation and clear next actions.

Please write this as if you're personally consulting with this creator - be friendly, professional, and specific. Reference your experience working with thousands of Dimeo creators and include relevant industry benchmarks.
"""
        
        return prompt

def plot_retention_curve(retention_data: Dict) -> go.Figure:
    """Creates a retention curve graph with Dimeo styling"""
    data_points = retention_data.get('data_points', [])
    
    if not data_points:
        fig = go.Figure()
        fig.add_annotation(
            text="No retention data available", 
            xref="paper", yref="paper", 
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        return fig
    
    df = pd.DataFrame(data_points)
    
    fig = go.Figure()
    
    # Dimeo-style retention curve
    fig.add_trace(go.Scatter(
        x=df['video_time_sec'],
        y=df['current_viewers'],
        mode='lines+markers',
        name='Active Viewers',
        line=dict(color='#1ab7ea', width=3),  # Dimeo blue
        marker=dict(size=6, color='#1ab7ea'),
        fill='tonexty',
        fillcolor='rgba(26, 183, 234, 0.1)',
        hovertemplate='<b>%{x}s</b><br>Viewers: %{y:,}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': "📈 Viewer Retention Curve",
            'font': {'size': 18, 'color': '#333'}
        },
        xaxis_title="Time (seconds)",
        yaxis_title="Active Viewers",
        hovermode='x unified',
        height=400,
        template="plotly_white",
        showlegend=False,
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def plot_retention_percentage(retention_data: Dict) -> go.Figure:
    """Creates a retention percentage graph with Dimeo styling"""
    data_points = retention_data.get('data_points', [])
    
    if not data_points:
        fig = go.Figure()
        fig.add_annotation(
            text="No retention data available", 
            xref="paper", yref="paper", 
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        return fig
    
    df = pd.DataFrame(data_points)
    
    fig = go.Figure()
    
    # Add industry benchmark line
    fig.add_hline(y=25, line_dash="dash", line_color="#ff6b6b", 
                  annotation_text="Industry Average", annotation_position="bottom right")
    
    fig.add_trace(go.Scatter(
        x=df['video_time_sec'],
        y=df['retention_percentage'],
        mode='lines+markers',
        name='Retention Rate',
        line=dict(color='#00d4aa', width=3),  # Dimeo green
        marker=dict(size=6, color='#00d4aa'),
        fill='tonexty',
        fillcolor='rgba(0, 212, 170, 0.1)',
        hovertemplate='<b>%{x}s</b><br>Retention: %{y:.1f}%<br><extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': "📊 Retention Percentage",
            'font': {'size': 18, 'color': '#333'}
        },
        xaxis_title="Time (seconds)",
        yaxis_title="Retention (%)",
        hovermode='x unified',
        yaxis=dict(range=[0, 100]),
        height=400,
        template="plotly_white",
        showlegend=False,
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def main():
    # Custom CSS for Dimeo-style design
    st.markdown("""
    <style>
    .main-header {
        color: #1ab7ea;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1ab7ea;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🎬 Dimeo Creator Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Professional video retention analysis by our expert team</p>', unsafe_allow_html=True)
    
    analyzer = RetentionAnalyzer()
    Dimeo_agent = DimeoAnalystAgent()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Analysis Settings")
        
        # Dropoff threshold
        threshold = st.slider(
            "📉 Dropoff Sensitivity (%)",
            min_value=5.0,
            max_value=50.0,
            value=10.0,
            step=5.0,
            help="Minimum percentage drop to flag as significant"
        )
        
        st.markdown("---")
        st.markdown("**🤖 AI Analyst Status:**")
        
        # Show API key status with appropriate styling
        status_msg, status_type = Dimeo_agent.get_status_message()
        if status_type == "success":
            st.success(status_msg)
        elif status_type == "warning":
            st.warning(status_msg)
        else:
            st.error(status_msg)
            
        st.markdown("*Requires OpenAI API key for full analysis*")
        
        # Debug info
        with st.expander("🔍 System Info"):
            st.write(f"API Endpoint: {API_BASE_URL}")
            st.write(f"API Key Status: {Dimeo_agent.api_key_status}")
            st.write(f"Key Present: {bool(OPENAI_API_KEY)}")
    
    # Connection status
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"🔗 Connected to: {API_BASE_URL}")
        with col2:
            videos = analyzer.get_videos()
            if videos:
                st.success(f"✅ {len(videos)} videos")
            else:
                st.error("❌ No data")
    
    if not videos:
        st.warning("⚠️ Unable to load video data. Please check your API connection.")
        st.code(f"curl {API_BASE_URL}/videos")
        return
    
    # Video selection
    st.header("🎥 Select Video for Analysis")
    
    video_options = {}
    for video in videos:
        viewers = video.get('unique_viewers', 'N/A')
        video_options[f"{video['video_id'][:12]}... ({viewers} viewers)"] = video['video_id']
    
    selected_video_display = st.selectbox(
        "Choose a video to analyze:",
        options=list(video_options.keys()),
        help="Select the video you want to get detailed retention insights for"
    )
    
    selected_video_id = video_options[selected_video_display]
    
    # Data retrieval with progress
    with st.spinner("📊 Loading analytics data..."):  
        retention_data = analyzer.get_retention_curve(selected_video_id)
        dropoffs_data = analyzer.get_dropoffs(selected_video_id, threshold)
        engagement_data = analyzer.get_engagement_summary(selected_video_id)
    
    # Key metrics display
    st.header("📈 Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_viewers = retention_data.get('total_unique_viewers', 0)
    avg_watch_time = engagement_data.get('average_watch_time_sec', 0)
    data_points = retention_data.get('data_points', [])
    video_duration = max([dp['video_time_sec'] for dp in data_points]) if data_points else 1
    completion_rate = (avg_watch_time / video_duration * 100) if video_duration > 0 else 0
    dropoffs_count = len(dropoffs_data.get('drop_offs', []))
    
    with col1:
        st.metric("👥 Unique Viewers", f"{total_viewers:,}",
                 help="Total number of people who watched this video")
    
    with col2:
        st.metric("⏱️ Avg Watch Time", f"{avg_watch_time:.1f}s",
                 help="Average time each viewer spent watching")
    
    with col3:
        delta_color = "normal" if completion_rate > 25 else "inverse"
        st.metric("✅ Completion Rate", f"{completion_rate:.1f}%", 
                 delta=f"{'Above' if completion_rate > 25 else 'Below'} average",
                 delta_color=delta_color,
                 help="Percentage of video watched on average")
    
    with col4:
        delta_color = "inverse" if dropoffs_count > 10 else "normal"
        st.metric("📉 Major Dropoffs", dropoffs_count,
                 delta=f"{'High' if dropoffs_count > 10 else 'Normal'} count",
                 delta_color=delta_color,
                 help="Number of significant viewer exit points")
    
    # Charts section
    st.header("📊 Retention Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_curve = plot_retention_curve(retention_data)
        st.plotly_chart(fig_curve, use_container_width=True)
    
    with col2:
        fig_percentage = plot_retention_percentage(retention_data)
        st.plotly_chart(fig_percentage, use_container_width=True)
    
    # Dropoff analysis
    if dropoffs_data.get('drop_offs'):
        st.header("📉 Critical Drop-off Points")
        
        dropoffs_df = pd.DataFrame(dropoffs_data['drop_offs'])
        
        # Sort by impact and show top 10
        top_dropoffs = dropoffs_df.nlargest(10, 'drop_off_percentage')
        
        st.dataframe(
            top_dropoffs[['video_time_sec', 'previous_viewers', 'current_viewers', 'drop_off_count', 'drop_off_percentage']],
            column_config={
                "video_time_sec": st.column_config.NumberColumn("Time", format="%ds"),
                "previous_viewers": st.column_config.NumberColumn("Before", format="%d"),
                "current_viewers": st.column_config.NumberColumn("After", format="%d"), 
                "drop_off_count": st.column_config.NumberColumn("Lost", format="%d"),
                "drop_off_percentage": st.column_config.NumberColumn("Impact", format="%.1f%%")
            },
            use_container_width=True,
            hide_index=True
        )
    
   
    st.header("🤖 Expert Analysis by Dimeo Team")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        analysis_button = st.button("🚀 Get Professional Analysis", type="primary", use_container_width=True)
    
    with col2:
        if Dimeo_agent.api_key_status == "valid":
            st.success("🟢 AI Ready")
        else:
            st.warning("🟡 Demo Mode")
    
    with col3:
        st.info("📊 Dimeo Expert")
    
    if analysis_button:
        with st.spinner("🧠 Sarah Chen is analyzing your video performance..."):
            analysis = Dimeo_agent.analyze_retention_data(
                selected_video_id, retention_data, dropoffs_data, engagement_data
            )
        
        st.markdown("### 📝 Professional Analysis Report")
        st.markdown(analysis)
        
        # Action items and save functionality
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Report", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Dimeo_retention_analysis_{selected_video_id[:8]}_{timestamp}.md"
                
                report_content = f"""# Dimeo Creator Analytics Report

**Video ID:** {selected_video_id}
**Analysis Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Analyst:** Sarah Chen, Senior Video Analytics Specialist
**Platform:** Dimeo Creator Services

## Performance Summary
- **Unique Viewers:** {total_viewers:,}
- **Average Watch Time:** {avg_watch_time:.1f} seconds
- **Completion Rate:** {completion_rate:.1f}%
- **Video Duration:** {video_duration} seconds
- **Critical Dropoffs:** {dropoffs_count}

## Detailed Expert Analysis
{analysis}

---
*Report generated by Dimeo Creator Analytics Platform*
*For questions about this analysis, contact creator-success@Dimeo.com*
"""
                
                st.download_button(
                    label="⬇️ Download Report (MD)",
                    data=report_content,
                    file_name=filename,
                    mime="text/markdown",
                    use_container_width=True
                )
        
        with col2:
            st.info("💡 **Next Step:** Implement the recommended changes and re-analyze in 1-2 weeks")
        
        with col3:
            st.success("🎯 **Goal:** Improve completion rate by 5-10% through targeted optimizations")

if __name__ == "__main__":
    main()