# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 09:41:52 2025

@author: CHECK
"""

import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import zipfile
import io
from openai import OpenAI
import urllib.parse
import sqlite3
import os
import google.generativeai as genai # ▼ 추가된 부분
def convert_history_to_genai_format(chat_history):
    genai_formatted_history = []
    for message in chat_history:
        # OpenAI의 'assistant' 역할을 Google Generative AI의 'model' 역할로 변경
        # 그리고 'content' 키 대신 'parts' 키를 사용합니다.
        role = "user" if message["role"] == "user" else "model"
        genai_formatted_history.append(
            {
                "role": role,
                "parts": [{"text": message["content"]}]
            }
        )
    return genai_formatted_history
# GPT + DB설계
# 페이지 설정
st.set_page_config(
    page_title="DART 기업분석 대시보드 + GPT 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 2rem;
    background: linear-gradient(90deg, #1f4e79, #2d5aa0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #1f4e79;
}

.warning-box {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}

.gpt-analysis {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
}

.db-info {
    background: #e8f5e8;
    border: 1px solid #4caf50;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── SerpAPI 설정 ────────────────────────────
#serp_api_key = "c4ebb9a234e85458c171ee43ec2c6f43601acca2cf08751d5900a19e53a5142b"
# ─── SerpAPI 설정 ────────────────────────────
serp_api_key = os.getenv("SERP_API_KEY", "c4ebb9a234e85458c171ee43ec2c6f43601acca2cf08751d5900a19e53a5142b")

# Streamlit secrets에서 읽기 시도
try:
    serp_api_key = st.secrets.get("SERP_API_KEY", serp_api_key)
except:
    pass

# -*- coding: utf-8 -*-
"""
배포환경 최적화 DartDB 클래스 - 세션 상태 기반
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import json

class DartDB:
    """배포환경 최적화 - 세션 상태 기반 데이터 저장"""
    
    def __init__(self, db_path=None):
        """배포환경에서는 세션 상태만 사용"""
        self.db_enabled = False  # 배포환경에서는 SQLite 비활성화
        self.db_path = None
        
        # 세션 상태 초기화
        if 'db_data' not in st.session_state:
            st.session_state.db_data = {
                'companies': [],
                'financial_data': [],
                'financial_metrics': [],
                'gpt_analysis': []
            }
        
        if 'db_enabled' not in st.session_state:
            st.session_state.db_enabled = False
        
        print("📋 배포환경: 세션 상태 기반 저장 시스템 활성화")
    
    def save_company(self, corp_code, corp_name, stock_code=None):
        """기업 정보 저장 - 세션 상태"""
        try:
            company_data = {
                'corp_code': corp_code,
                'corp_name': corp_name,
                'stock_code': stock_code or '',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 중복 제거 후 추가
            existing = [c for c in st.session_state.db_data['companies'] 
                       if c.get('corp_code') != corp_code]
            existing.append(company_data)
            st.session_state.db_data['companies'] = existing
            
            print(f"✅ 기업 정보 저장: {corp_name}")
            return True
            
        except Exception as e:
            print(f"❌ 기업 정보 저장 실패: {e}")
            st.error(f"❌ 기업 정보 저장 실패: {e}")
            return False
    
    def save_financial_data(self, corp_code, year, report_type, financial_df):
        """재무 데이터 저장 - 세션 상태"""
        try:
            saved_count = 0
            
            for _, row in financial_df.iterrows():
                financial_record = {
                    'corp_code': corp_code,
                    'year': year,
                    'report_type': report_type,
                    'account_nm': row.get('account_nm', ''),
                    'thstrm_amount': str(row.get('thstrm_amount', '')),
                    'frmtrm_amount': str(row.get('frmtrm_amount', '')),
                    'bfefrmtrm_amount': str(row.get('bfefrmtrm_amount', '')),
                    'fs_div': row.get('fs_div', ''),
                    'created_at': datetime.now().isoformat()
                }
                st.session_state.db_data['financial_data'].append(financial_record)
                saved_count += 1
            
            if saved_count > 0:
                st.success(f"💾 재무 데이터 {saved_count}건이 저장되었습니다!")
                return True
            else:
                st.warning("⚠️ 저장된 재무 데이터가 없습니다.")
                return False
            
        except Exception as e:
            print(f"❌ 재무 데이터 저장 실패: {e}")
            st.error(f"❌ 재무 데이터 저장 실패: {e}")
            return False
    
    def save_financial_metrics(self, corp_code, corp_name, year, report_type, metrics, ratios):
        """재무 지표 요약 저장 - 세션 상태"""
        try:
            metrics_record = {
                'corp_code': corp_code,
                'corp_name': corp_name,
                'year': year,
                'report_type': report_type,
                'revenue': metrics.get('매출액', 0),
                'operating_profit': metrics.get('영업이익', 0),
                'net_income': metrics.get('당기순이익', 0),
                'total_assets': metrics.get('자산총계', 0),
                'total_liabilities': metrics.get('부채총계', 0),
                'total_equity': metrics.get('자본총계', 0),
                'operating_margin': ratios.get('영업이익률', 0),
                'net_margin': ratios.get('순이익률', 0),
                'roe': ratios.get('ROE', 0),
                'roa': ratios.get('ROA', 0),
                'debt_ratio': ratios.get('부채비율', 0),
                'created_at': datetime.now().isoformat()
            }
            
            # 기존 동일 데이터 제거 후 추가
            existing = [m for m in st.session_state.db_data['financial_metrics'] 
                       if not (m.get('corp_code') == corp_code and 
                              m.get('year') == year and 
                              m.get('report_type') == report_type)]
            existing.append(metrics_record)
            st.session_state.db_data['financial_metrics'] = existing
            
            st.success("💾 재무 지표가 저장되었습니다!")
            return True
            
        except Exception as e:
            print(f"❌ 재무 지표 저장 실패: {e}")
            st.error(f"❌ 재무 지표 저장 실패: {e}")
            return False
    
    def save_gpt_analysis(self, corp_code, corp_name, question, answer, used_web_search=False):
        """GPT 분석 결과 저장 - 세션 상태"""
        try:
            analysis_record = {
                'corp_code': corp_code,
                'corp_name': corp_name,
                'question': question,
                'answer': answer,
                'used_web_search': used_web_search,
                'created_at': datetime.now().isoformat()
            }
            
            st.session_state.db_data['gpt_analysis'].append(analysis_record)
            return True
            
        except Exception as e:
            print(f"❌ GPT 분석 저장 실패: {e}")
            return False
    
    def get_companies(self):
        """저장된 기업 목록 조회 - 세션 상태"""
        try:
            companies = st.session_state.db_data.get('companies', [])
            if companies:
                df = pd.DataFrame(companies)
                # 최신순 정렬
                if 'updated_at' in df.columns:
                    df = df.sort_values('updated_at', ascending=False)
                return df
            else:
                return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ 기업 목록 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_financial_metrics(self, corp_code=None, limit=10):
        """재무 지표 조회 - 세션 상태"""
        try:
            metrics = st.session_state.db_data.get('financial_metrics', [])
            
            if corp_code:
                metrics = [m for m in metrics if m.get('corp_code') == corp_code]
            
            # 최신순 정렬
            metrics = sorted(metrics, key=lambda x: x.get('created_at', ''), reverse=True)
            
            return pd.DataFrame(metrics[:limit])
            
        except Exception as e:
            print(f"❌ 재무 지표 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_gpt_analysis_history(self, corp_code=None, limit=10):
        """GPT 분석 기록 조회 - 세션 상태"""
        try:
            analysis = st.session_state.db_data.get('gpt_analysis', [])
            
            if corp_code:
                analysis = [a for a in analysis if a.get('corp_code') == corp_code]
            
            # 최신순 정렬
            analysis = sorted(analysis, key=lambda x: x.get('created_at', ''), reverse=True)
            
            return pd.DataFrame(analysis[:limit])
            
        except Exception as e:
            print(f"❌ GPT 분석 기록 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_db_stats(self):
        """데이터베이스 통계 조회 - 세션 상태"""
        try:
            stats = {
                'companies': len(st.session_state.db_data.get('companies', [])),
                'financial_records': len(st.session_state.db_data.get('financial_data', [])),
                'financial_metrics': len(st.session_state.db_data.get('financial_metrics', [])),
                'gpt_analysis': len(st.session_state.db_data.get('gpt_analysis', [])),
                'db_size': 0.0  # 세션 메모리는 크기 측정 불가
            }
            return stats
            
        except Exception as e:
            print(f"❌ DB 통계 조회 실패: {e}")
            return {
                'companies': 0,
                'financial_records': 0,
                'financial_metrics': 0,
                'gpt_analysis': 0,
                'db_size': 0.0
            }
    
    def export_db_json(self):
        """DB 데이터를 JSON으로 내보내기 - 세션 상태"""
        try:
            export_data = st.session_state.db_data.copy()
            return export_data
            
        except Exception as e:
            print(f"❌ DB 내보내기 실패: {e}")
            st.error(f"❌ DB 내보내기 실패: {e}")
            return None
    
    def import_db_json(self, json_data):
        """JSON 데이터를 DB로 가져오기 - 세션 상태"""
        try:
            # 기존 데이터에 새 데이터 병합
            for table_name, records in json_data.items():
                if table_name in st.session_state.db_data and records:
                    existing = st.session_state.db_data[table_name]
                    
                    if table_name == 'companies':
                        # 기업은 corp_code 기준으로 중복 제거
                        existing_codes = {c.get('corp_code') for c in existing}
                        new_records = [r for r in records if r.get('corp_code') not in existing_codes]
                        st.session_state.db_data[table_name].extend(new_records)
                    
                    elif table_name == 'financial_metrics':
                        # 재무지표는 corp_code + year + report_type 기준으로 중복 제거
                        existing_keys = {(m.get('corp_code'), m.get('year'), m.get('report_type')) 
                                       for m in existing}
                        new_records = [r for r in records 
                                     if (r.get('corp_code'), r.get('year'), r.get('report_type')) not in existing_keys]
                        st.session_state.db_data[table_name].extend(new_records)
                    
                    else:
                        # 나머지는 그냥 추가
                        st.session_state.db_data[table_name].extend(records)
            
            return True
            
        except Exception as e:
            print(f"❌ DB 가져오기 실패: {e}")
            st.error(f"❌ DB 가져오기 실패: {e}")
            return False
    
    def clear_all_data(self):
        """모든 데이터 삭제 - 세션 상태"""
        try:
            st.session_state.db_data = {
                'companies': [],
                'financial_data': [],
                'financial_metrics': [],
                'gpt_analysis': []
            }
            return True
            
        except Exception as e:
            print(f"❌ 데이터 삭제 실패: {e}")
            return False
    
    def get_deployment_info(self):
        """배포환경 정보 반환"""
        return {
            'environment': 'deployment',
            'storage_type': 'session_state',
            'persistent': False,
            'backup_recommended': True,
            'data_retention': 'session_only'
        }

# 배포환경 전용 유틸리티 함수들
def show_deployment_warning():
    """배포환경 경고 표시"""
    st.warning("""
    ⚠️ **배포환경 알림**
    - 데이터는 브라우저 세션에만 저장됩니다
    - 브라우저를 새로고침하거나 닫으면 데이터가 삭제됩니다
    - 중요한 분석 결과는 JSON 백업 파일로 다운로드하세요
    """)

def show_data_persistence_info():
    """데이터 지속성 정보 표시"""
    st.info("""
    💡 **데이터 보관 방법**
    
    **✅ 현재 세션 중:**
    - 모든 분석 데이터가 메모리에 저장됨
    - 페이지 이동해도 데이터 유지
    
    **📥 장기 보관:**
    - DB 관리 탭에서 "💾 DB를 JSON으로 백업" 클릭
    - 백업 파일을 컴퓨터에 저장
    - 다음 사용 시 백업 파일 업로드하여 복원
    """)

def optimize_session_performance():
    """세션 성능 최적화"""
    try:
        # 각 데이터 타입별 최대 보관 개수 제한
        limits = {
            'companies': 50,           # 최대 50개 기업
            'financial_data': 1000,    # 최대 1000건 재무데이터
            'financial_metrics': 100,  # 최대 100건 재무지표
            'gpt_analysis': 50         # 최대 50건 GPT 분석
        }
        
        for data_type, limit in limits.items():
            if data_type in st.session_state.db_data:
                data_list = st.session_state.db_data[data_type]
                if len(data_list) > limit:
                    # 최신 데이터만 유지 (created_at 기준)
                    sorted_data = sorted(data_list, 
                                       key=lambda x: x.get('created_at', ''), 
                                       reverse=True)
                    st.session_state.db_data[data_type] = sorted_data[:limit]
                    print(f"📊 {data_type} 데이터 최적화: {len(data_list)} → {limit}건")
        
        return True
        
    except Exception as e:
        print(f"❌ 세션 최적화 실패: {e}")
        return False
# ── SerpAPI 검색 함수 (개선된 버전) - 디버깅 강화 ───────────────────────────
def search_serpapi(query, num=5, engine="google", location="South Korea", hl="ko"):
    """
    SerpAPI를 사용한 실시간 웹 검색
    """
    params = {
        "engine": engine,
        "q": query,
        "api_key": serp_api_key,
        "num": num,
        "location": location,
        "hl": hl,
        "gl": "kr"  # 국가 코드 (한국)
    }
    
    url = "https://serpapi.com/search.json"
    
    try:
        # API 호출 상태 표시
        print(f"🔍 SerpAPI 호출: {query}")
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        # API 응답 상태 확인
        if "error" in data:
            error_msg = f"❌ SerpAPI 오류: {data['error']}"
            print(error_msg)
            return error_msg
        
        organic_results = data.get("organic_results", [])
        print(f"📊 검색 결과 수: {len(organic_results)}")
        
        if not organic_results:
            return "⚠️ 검색 결과가 없습니다."
        
        # 검색 결과 포맷팅
        items = []
        for i, result in enumerate(organic_results[:num], 1):
            title = result.get("title", "제목 없음")
            snippet = result.get("snippet", "요약 없음")
            link = result.get("link", "#")
            date = result.get("date", "")
            
            # 날짜 정보가 있으면 포함
            date_info = f" ({date})" if date else ""
            
            items.append(f"""
**{i}. {title}**{date_info}
{snippet}
🔗 [원문 보기]({link})
""")
        
        search_summary = f"✅ 총 {len(organic_results)}개 결과 중 {len(items)}개 표시"
        final_result = f"{search_summary}\n\n" + "\n---\n".join(items)
        
        print(f"✅ 검색 완료: {len(final_result)}자")
        return final_result
        
    except requests.exceptions.Timeout:
        error_msg = "⏰ 검색 시간 초과: 네트워크 연결을 확인해주세요."
        print(error_msg)
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"🌐 네트워크 오류: {e}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ 검색 오류: {e}"
        print(error_msg)
        return error_msg

# ── 뉴스 검색 전용 함수 - 디버깅 강화 ───────────────────────────
def search_news_serpapi(query, num=3):
    """뉴스 전용 검색 함수"""
    params = {
        "engine": "google",
        "q": query,
        "api_key": serp_api_key,
        "tbm": "nws",  # 뉴스 검색
        "num": num,
        "location": "South Korea",
        "hl": "ko",
        "gl": "kr"
    }
    
    url = "https://serpapi.com/search.json"
    
    try:
        print(f"📰 뉴스 검색: {query}")
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if "error" in data:
            error_msg = f"❌ 뉴스 검색 오류: {data['error']}"
            print(error_msg)
            return error_msg
        
        news_results = data.get("news_results", [])
        print(f"📊 뉴스 결과 수: {len(news_results)}")
        
        if not news_results:
            return "📰 관련 뉴스가 없습니다."
        
        items = []
        for i, news in enumerate(news_results[:num], 1):
            title = news.get("title", "제목 없음")
            snippet = news.get("snippet", "")
            link = news.get("link", "#")
            date = news.get("date", "")
            source = news.get("source", "출처 불명")
            
            date_info = f" | {date}" if date else ""
            
            items.append(f"""
**📰 {i}. {title}**
*출처: {source}{date_info}*
{snippet}
🔗 [뉴스 원문]({link})
""")
        
        final_result = f"📰 **최신 뉴스** (총 {len(news_results)}건 중 {len(items)}건)\n\n" + "\n---\n".join(items)
        print(f"✅ 뉴스 검색 완료: {len(final_result)}자")
        return final_result
        
    except Exception as e:
        error_msg = f"❌ 뉴스 검색 오류: {e}"
        print(error_msg)
        return error_msg

# DART API 클래스
class DartAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
    
    def get_corp_list(self):
        """전체 기업 리스트 조회 (ZIP 파일 처리)"""
        url = f"{self.base_url}/corpCode.xml"
        params = {'crtfc_key': self.api_key}
        
        try:
            st.info("🔄 DART API에서 기업 리스트를 다운로드 중입니다...")
            
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # ZIP 파일 처리
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                file_list = zip_file.namelist()
                xml_content = zip_file.read(file_list[0])
                
                # XML 파싱
                root = ET.fromstring(xml_content.decode('utf-8'))
                
                # 상태 확인
                status_elem = root.find('.//status')
                if status_elem is not None and status_elem.text != '000':
                    message_elem = root.find('.//message')
                    error_msg = message_elem.text if message_elem is not None else '알 수 없는 오류'
                    st.error(f"❌ API 오류: {error_msg}")
                    return self._get_fallback_corp_list()
                
                # 기업 데이터 추출
                corps = []
                for corp in root.findall('.//list'):
                    corp_data = {}
                    for child in corp:
                        corp_data[child.tag] = child.text if child.text else ""
                    corps.append(corp_data)
                
                if corps:
                    df = pd.DataFrame(corps)
                    # 상장회사만 필터링
                    if 'stock_code' in df.columns:
                        df_listed = df[df['stock_code'].notna() & (df['stock_code'] != '')]
                        st.success(f"✅ 총 {len(df)}개 기업 중 {len(df_listed)}개 상장기업 데이터 로드 완료")
                        return df_listed
                    else:
                        st.success(f"✅ 총 {len(df)}개 기업 데이터 로드 완료")
                        return df
                        
        except Exception as e:
            st.error(f"❌ 기업 리스트 로드 실패: {e}")
            return self._get_fallback_corp_list()
    
    def _get_fallback_corp_list(self):
        """API 실패 시 주요 기업 리스트"""
        fallback_data = [
            {'corp_name': '삼성전자', 'corp_code': '00126380', 'stock_code': '005930'},
            {'corp_name': 'SK하이닉스', 'corp_code': '00164779', 'stock_code': '000660'},
            {'corp_name': 'LG전자', 'corp_code': '00401731', 'stock_code': '066570'},
            {'corp_name': '현대자동차', 'corp_code': '00164742', 'stock_code': '005380'},
            {'corp_name': 'NAVER', 'corp_code': '00293886', 'stock_code': '035420'},
            {'corp_name': '카카오', 'corp_code': '00401731', 'stock_code': '035720'},
            {'corp_name': '포스코홀딩스', 'corp_code': '00434003', 'stock_code': '005490'},
            {'corp_name': 'SK텔레콤', 'corp_code': '00269514', 'stock_code': '017670'}
        ]
        
        st.warning("⚠️ 전체 기업 리스트를 불러올 수 없어 주요 기업 리스트를 제공합니다.")
        return pd.DataFrame(fallback_data)
    
    def get_company_info(self, corp_code):
        """기업 기본정보 조회 - 공시검색 API 활용"""
        current_year = datetime.now().year
        url = f"{self.base_url}/list.json"
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code,
            'bgn_de': f'{current_year-1}0101',  # 작년부터
            'end_de': f'{current_year}1231',    # 올해까지
            'last_reprt_at': 'Y',
            'pblntf_ty': 'A',
            'page_no': '1',
            'page_count': '1'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '000' and data.get('list'):
                first_report = data['list'][0]
                # 실제 API에서 제공되는 정보만 포함
                company_info = {
                    'corp_name': first_report.get('corp_name', ''),
                    'corp_code': corp_code,
                    'stock_code': first_report.get('stock_code', ''),
                    'modify_date': first_report.get('modify_date', ''),
                    'corp_cls': first_report.get('corp_cls', '')
                }
                return {'status': '000', 'list': [company_info]}
            else:
                st.warning(f"기업정보 조회 실패: {data.get('message', '데이터 없음')}")
                return None
                
        except Exception as e:
            st.error(f"기업 정보 조회 실패: {e}")
            return None
    
    def get_financial_statements(self, corp_code, bsns_year, reprt_code='11011'):
        """재무제표 조회"""
        url = f"{self.base_url}/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code,
            'bsns_year': str(bsns_year),
            'reprt_code': reprt_code,
            'fs_div': 'OFS'  # 연결재무제표:CFS, 재무제표:OFS
        }
        
        try:
            st.info(f"🔍 재무제표 조회 중... (기업코드: {corp_code}, 연도: {bsns_year})")
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == '000':
                if data.get('list') and len(data['list']) > 0:
                    st.success(f"✅ 재무데이터 {len(data['list'])}건 조회 성공")
                    return data
                else:
                    st.warning("⚠️ 재무데이터가 비어있습니다.")
                    return None
                    
            elif data.get('status') == '013':
                # 연결재무제표가 없으면 개별재무제표 시도
                st.info("🔄 연결재무제표가 없어 개별재무제표로 재시도...")
                params['fs_div'] = 'OFS'
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == '000' and data.get('list'):
                    st.success(f"✅ 개별재무제표 {len(data['list'])}건 조회 성공")
                    return data
                else:
                    # 자연스러운 메시지 표시
                    current_year = datetime.now().year
                    current_month = datetime.now().month
                    
                    if int(bsns_year) == current_year:
                        if reprt_code == '11011':  # 사업보고서
                            if current_month < 4:  # 4월 이전
                                st.info("📅 사업보고서는 통상 3월 말에 공시됩니다. 아직 공시되지 않았습니다.")
                            else:
                                st.warning("⚠️ 사업보고서가 아직 공시되지 않았습니다.")
                        elif reprt_code == '11012':  # 반기보고서
                            if current_month < 9:  # 9월 이전
                                st.info("📅 반기보고서는 통상 8월 말에 공시됩니다. 아직 공시되지 않았습니다.")
                            else:
                                st.warning("⚠️ 반기보고서가 아직 공시되지 않았습니다.")
                        elif reprt_code == '11013':  # 1분기보고서
                            if current_month < 6:  # 6월 이전
                                st.info("📅 1분기보고서는 통상 5월 말에 공시됩니다. 아직 공시되지 않았습니다.")
                            else:
                                st.warning("⚠️ 1분기보고서가 아직 공시되지 않았습니다.")
                        elif reprt_code == '11014':  # 3분기보고서
                            if current_month < 12:  # 12월 이전
                                st.info("📅 3분기보고서는 통상 11월 말에 공시됩니다. 아직 공시되지 않았습니다.")
                            else:
                                st.warning("⚠️ 3분기보고서가 아직 공시되지 않았습니다.")
                    else:
                        st.warning(f"⚠️ {bsns_year}년도 재무제표 데이터를 찾을 수 없습니다.")
                    
                    return None
            else:
                # 기타 오류 메시지도 자연스럽게 변경
                error_msg = data.get('message', '알 수 없는 오류')
                if 'OpenDART' in error_msg or '개별재무제표' in error_msg:
                    st.warning("⚠️ 해당 연도의 재무제표가 아직 공시되지 않았습니다.")
                else:
                    st.warning(f"⚠️ 재무제표 조회 실패: {error_msg}")
                return None
                
        except Exception as e:
            st.error(f"❌ 재무제표 조회 실패: {e}")
            return None

def extract_key_metrics(df_financial):
    """재무제표에서 주요 지표 추출 (‘부채 및 자본총계’ 제외 추가)"""
    metrics = {}
    
    # 전기 금액 컬럼명 탐색 (기존 로직 그대로)
    prev_amount_col = None
    possible_prev_cols = ['frmtrm_amount', 'bfefrmtrm_amount', 'prev_amount', 'before_amount']
    for col in possible_prev_cols:
        if col in df_financial.columns:
            prev_amount_col = col
            break
    
    account_mapping = {
        #'매출액':      ['매출액', '수익(매출액)', '매출', '영업수익', '매출총액'],
        '영업이익':    ['영업이익', '영업이익(손실)', '영업손익'],
        '당기순이익':  ['당기순이익', '당기순이익(손실)', '순이익', '당기순손익'],
        '자산총계':    ['자산총계', '자산총액', '총자산'],
        '부채총계':    ['부채총계', '부채총액', '총부채'],
        '자본총계':    ['자본총계', '자본총액', '자본금', '총자본', '자본']
    }
    
    for metric_name, account_names in account_mapping.items():
        for account_name in account_names:
            # 계정명에 해당 키워드가 포함된 행들
            candidate = df_financial[df_financial['account_nm'].str.contains(account_name, na=False)]
            
            # “부채 및 자본총계” 행은 제외
            if metric_name in ('부채총계', '자본총계'):
                # 계정명에 “부채”와 “자본”이 모두 쓰인 합계 행 필터링
                candidate = candidate[~candidate['account_nm'].str.contains('부채.*자본|자본.*부채')]
            
            if not candidate.empty:
                # 당기 금액
                val = candidate.iloc[0]['thstrm_amount']
                val = int(str(val).replace(',', '').replace('-', '')) if pd.notna(val) else 0
                metrics[metric_name] = val
                
                # 전기 금액 (있다면)
                if prev_amount_col and prev_amount_col in candidate.columns:
                    prev_val = candidate.iloc[0][prev_amount_col]
                    if pd.notna(prev_val):
                        pv = int(str(prev_val).replace(',', '').replace('-', ''))
                        metrics[f"{metric_name}_전기"] = pv
                break
    
    return metrics



def calculate_financial_ratios(metrics):
    """재무 비율 계산"""
    ratios = {}
    
    try:
        if metrics.get('매출액', 0) > 0:
            # 영업이익률
            if metrics.get('영업이익'):
                ratios['영업이익률'] = (metrics['영업이익'] / metrics['매출액']) * 100
            
            # 순이익률
            if metrics.get('당기순이익'):
                ratios['순이익률'] = (metrics['당기순이익'] / metrics['매출액']) * 100
        
        if metrics.get('자본총계', 0) > 0:
            # ROE
            if metrics.get('당기순이익'):
                ratios['ROE'] = (metrics['당기순이익'] / metrics['자본총계']) * 100
            
            # 부채비율
            if metrics.get('부채총계'):
                ratios['부채비율'] = (metrics['부채총계'] / metrics['자본총계']) * 100
        
        if metrics.get('자산총계', 0) > 0:
            # ROA
            if metrics.get('당기순이익'):
                ratios['ROA'] = (metrics['당기순이익'] / metrics['자산총계']) * 100
    
    except Exception as e:
        st.warning(f"재무 비율 계산 오류: {e}")
    
    return ratios

# ─── 챗 히스토리 초기화 ────────────────────────────────────────────────────
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# 메인 애플리케이션
def main():
    st.markdown('<h1 class="main-header">📊 DART 기업분석 대시보드 + AI 분석 + 💾 DB</h1>', unsafe_allow_html=True)
    
    # API 키 설정
    dart_api_key = "cab55bc55fe7483099eddb56af81d89360ba34f5"
    # API 키 설정 (환경 변수에서 읽기)
    dart_api_key = os.getenv("DART_API_KEY", "cab55bc55fe7483099eddb56af81d89360ba34f5")
    
    # Streamlit secrets에서도 읽기 시도
    try:
        dart_api_key = st.secrets.get("DART_API_KEY", dart_api_key)
    except:
        pass

    dart_api = DartAPI(dart_api_key)
    
    # DB 초기화
    db = DartDB()
    
    # 사이드바
    with st.sidebar:
        st.header("🔧 설정")
        
        # ▼ 변경/추가된 부분: AI 모델 선택 기능 추가
        st.header("⚫ AI 모델 & 검색 설정")
        selected_model = st.selectbox(
            "🤖 AI 모델 선택", 
            ("GPT-4o", "Gemma 3 27b"),
            help="분석에 사용할 AI 모델을 선택하세요. 모델에 맞는 API 키가 필요합니다."
        )
        
        openai_api_key = st.text_input("🔑 OpenAI API 키", type="password")
        google_api_key = st.text_input("🔑 Google AI API 키", type="password")
        # ▲ 변경/추가된 부분
        
        use_serpapi = st.checkbox("📡 실시간 웹 검색 사용 (SerpAPI)", value=True)
        
# ─── 새 기능: DB 저장 설정 ──────────────────────────────
        st.header("💾 데이터베이스 설정")
        save_to_db = st.checkbox("📀 분석 데이터 DB 저장", value=True, help="기업정보, 재무데이터, AI 분석 결과를 SQLite DB에 저장합니다")
        
        # ... (이하 사이드바의 나머지 부분은 기존 코드와 동일) ...
        
        # DB 통계 표시
        if st.button("📊 DB 현황 보기"):
            stats = db.get_db_stats()
            if stats:
                st.markdown('<div class="db-info">', unsafe_allow_html=True)
                st.markdown("**💾 데이터베이스 현황**")
                st.write(f"🏢 저장된 기업: {stats.get('companies', 0)}개")
                st.write(f"📊 재무 기록: {stats.get('financial_records', 0)}건")
                st.write(f"📈 재무 지표: {stats.get('financial_metrics', 0)}건")
                st.write(f"🤖 AI 분석: {stats.get('gpt_analysis', 0)}건")
                st.write(f"💽 DB 크기: {stats.get('db_size', 0):.2f}MB")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 저장된 기업 목록 표시
        with st.expander("💾 저장된 기업 목록", expanded=False):
            saved_companies = db.get_companies()
            if not saved_companies.empty:
                for _, company in saved_companies.head(10).iterrows():
                    stock_info = f" ({company['stock_code']})" if company['stock_code'] else " (비상장)"
                    st.write(f"🏢 {company['corp_name']}{stock_info}")
                if len(saved_companies) > 10:
                    st.write(f"... 외 {len(saved_companies)-10}개 기업")
            else:
                st.write("저장된 기업이 없습니다.")
        
        # 기업 선택
        st.header("🏢 기업 선택")
        
        # 기업 리스트 로드
        if 'corp_list' not in st.session_state or st.button("🔄 기업 리스트 새로고침"):
            with st.spinner("기업 리스트를 불러오는 중..."):
                st.session_state.corp_list = dart_api.get_corp_list()
        
        corp_list = st.session_state.get('corp_list', pd.DataFrame())
        
        selected_corp_name = None
        selected_corp_code = None
        
        if not corp_list.empty:
            search_term = st.text_input("기업명 검색", placeholder="삼성전자, LG전자 등")
            
            if search_term:
                filtered_corps = corp_list[
                    corp_list['corp_name'].str.contains(search_term, na=False, case=False)
                ].head(20)
                
                if not filtered_corps.empty:
                    st.write(f"🔍 '{search_term}' 검색 결과: {len(filtered_corps)}개")
                    
                    corp_options = []
                    
                    for idx, row in filtered_corps.iterrows():
                        corp_name = str(row['corp_name']).strip()
                        stock_code = str(row.get('stock_code', '')).strip()
                        corp_code = str(row['corp_code']).strip()
                        
                        display_name = f"{corp_name} ({stock_code})" if stock_code and stock_code != 'nan' and stock_code != '' else f"{corp_name} (비상장)"
                        
                        corp_options.append({
                            'display': display_name,
                            'corp_name': corp_name,
                            'corp_code': corp_code,
                            'stock_code': stock_code if stock_code != 'nan' else '',
                            'index': idx
                        })
                    
                    option_displays = ["선택하세요..."] + [option['display'] for option in corp_options]
                    
                    selected_display = st.selectbox(
                        "기업 선택", 
                        option_displays,
                        index=0,
                        key=f"corp_select_{search_term}"
                    )
                    
                    if selected_display and selected_display != "선택하세요...":
                        selected_option = next((opt for opt in corp_options if opt['display'] == selected_display), None)
                        
                        if selected_option:
                            selected_corp_name = selected_option['corp_name']
                            selected_corp_code = selected_option['corp_code']
                            
                            st.success(f"✅ {selected_corp_name} 선택됨")
                            if selected_option['stock_code']:
                                st.info(f"주식코드: {selected_option['stock_code']}")
                            st.info(f"기업코드: {selected_corp_code}")
                    else:
                        selected_corp_name = None
                        selected_corp_code = None
                else:
                    st.warning("❌ 검색 결과가 없습니다.")
        else:
            st.error("❌ 기업 리스트를 불러올 수 없습니다.")
        
        st.header("📊 분석 설정")
        
        current_year = datetime.now().year
        year_options = list(range(current_year, current_year - 6, -1))
        
        analysis_year = st.selectbox(
            "분석 연도", 
            year_options, 
            index=0,
            help=f"가장 최신 데이터는 {current_year}년입니다"
        )
        
        report_options = {
            "사업보고서": "11011", "반기보고서": "11012", 
            "1분기보고서": "11013", "3분기보고서": "11014"
        }
        report_type = st.selectbox("보고서 유형", list(report_options.keys()))
        report_code = report_options[report_type]
    
    # 메인 콘텐츠
    if selected_corp_code and selected_corp_name:
        st.markdown(f"## 🏢 {selected_corp_name} 분석")
        
        with st.spinner("데이터를 불러오는 중..."):
            company_info = dart_api.get_company_info(selected_corp_code)
            financial_data = dart_api.get_financial_statements(
                selected_corp_code, str(analysis_year), report_code
            )
        
        # DB 저장 (설정에서 활성화한 경우)
        if save_to_db:
            save_success = []
            
            # 기업 정보 저장
            if company_info and company_info.get('list'):
                info = company_info['list'][0]
                if db.save_company(
                    selected_corp_code, 
                    info.get('corp_name', ''), 
                    info.get('stock_code', '')
                ):
                    save_success.append("기업 정보")
            
            # 재무 데이터 저장
            if financial_data and financial_data.get('list'):
                df_financial = pd.DataFrame(financial_data['list'])
                if db.save_financial_data(selected_corp_code, analysis_year, report_type, df_financial):
                    save_success.append("재무 데이터")
            
            # 종합 결과 표시
            if save_success:
                st.info(f"💾 저장 완료: {', '.join(save_success)}")
            else:
                st.warning("⚠️ 저장할 데이터가 없거나 저장에 실패했습니다.")
        
        # 탭 생성 - DB 관리 탭 추가
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 기업 정보", "💰 재무 분석", "📊 시각화", "📑 공시 정보", "🤖 GPT 분석", "💾 DB 관리"])
        
        # 탭 1: 기업 정보
        with tab1:
            st.markdown("### 📋 기본 정보")
            
            if company_info and company_info.get('list'):
                info = company_info['list'][0]
                
                # 실제 API에서 제공되는 정보만 표시
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("기업명", info.get('corp_name', 'N/A'))
                
                with col2:
                    st.metric("기업코드", info.get('corp_code', 'N/A'))
                
                with col3:
                    stock_code = info.get('stock_code', 'N/A')
                    st.metric("주식코드", stock_code if stock_code else '비상장')
                
                # 추가 정보가 있다면 표시
                if any([info.get('modify_date'), info.get('corp_cls')]):
                    st.markdown("#### 📊 추가 정보")
                    add_col1, add_col2 = st.columns(2)
                    
                    if info.get('modify_date'):
                        with add_col1:
                            st.write(f"**정보 수정일:** {info.get('modify_date')}")
                    
                    if info.get('corp_cls'):
                        with add_col2:
                            corp_type = "상장기업" if info.get('corp_cls') == 'Y' else "비상장기업"
                            st.write(f"**기업 구분:** {corp_type}")
                
                st.info("💡 DART API는 기본 식별 정보만 제공합니다. 상세 정보는 각 탭에서 확인하세요.")
            else:
                st.warning("기업 정보를 불러올 수 없습니다.")
        
        # 탭 2: 재무 분석
        with tab2:
            st.markdown("### 💰 재무 분석")
            
            if financial_data and financial_data.get('list'):
                df_financial = pd.DataFrame(financial_data['list'])
                
                # 주요 재무 지표 추출
                metrics = extract_key_metrics(df_financial)
                
                if metrics:
                    # 주요 지표 표시
                    st.markdown("#### 📈 주요 재무 지표")
                    
                    cols = st.columns(3)
                    
                    # 표시할 지표들 정의 (당기 데이터 우선, 자본총계 포함)
                    display_metrics = []
                    
                    # 기본 당기 지표들
                    basic_metrics = ['매출액', '영업이익', '당기순이익', '자산총계', '부채총계', '자본총계']
                    for metric in basic_metrics:
                        if metric in metrics:
                            display_metrics.append((metric, metrics[metric]))
                    
                    # 6개를 채우기 위해 전기 데이터가 있다면 추가 (자본총계 제외)
                    if len(display_metrics) < 6:
                        for metric in ['매출액', '영업이익', '당기순이익', '자산총계', '부채총계']:
                            prev_key = f"{metric}_전기"
                            if prev_key in metrics and len(display_metrics) < 6:
                                display_metrics.append((f"{metric}_전기", metrics[prev_key]))
                    
                    # 최대 6개 지표 표시
                    for i, (metric, value) in enumerate(display_metrics[:6]):
                        col_idx = i % 3
                        with cols[col_idx]:
                            if value >= 0:
                                st.metric(label=metric, value=f"{value/1e12:.2f}조원")
                            else:
                                st.metric(label=metric, value=f"({abs(value)/1e12:.2f})조원")
                    
                    # 재무 비율
                    ratios = calculate_financial_ratios(metrics)
                    
                    if ratios:
                        st.markdown("#### 📊 재무 비율")
                        ratio_cols = st.columns(len(ratios))
                        
                        for i, (ratio, value) in enumerate(ratios.items()):
                            with ratio_cols[i]:
                                st.metric(ratio, f"{value:.2f}%")
                    
                    # DB 저장 (재무 지표) - 설정에서 활성화한 경우
                    if save_to_db:
                        db.save_financial_metrics(selected_corp_code, selected_corp_name, analysis_year, report_type, metrics, ratios)
                
                # 상세 재무제표
                with st.expander("📊 상세 재무제표 보기", expanded=False):
                    if 'account_nm' in df_financial.columns:
                        # 전기 금액 컬럼명 확인 및 처리
                        prev_amount_col = None
                        possible_prev_cols = ['frmtrm_amount', 'bfefrmtrm_amount', 'prev_amount', 'before_amount']
                        
                        for col in possible_prev_cols:
                            if col in df_financial.columns:
                                prev_amount_col = col
                                break
                        
                        # 표시할 컬럼 선택 (당기 금액만)
                        display_columns = ['account_nm', 'thstrm_amount']
                        column_names = ['계정과목', '당기금액']
                        
                        # 데이터 프레임 생성
                        display_df = df_financial[display_columns].copy()
                        display_df.columns = column_names
                        
                        # 금액 데이터 포맷팅 함수 개선
                        def format_amount(value):
                            """금액 데이터를 안전하게 포맷팅"""
                            if pd.isna(value) or value is None:
                                return "N/A"
                            
                            # 문자열로 변환
                            str_value = str(value).strip()
                            
                            # 빈 문자열이거나 'None'인 경우
                            if not str_value or str_value.lower() == 'none':
                                return "N/A"
                            
                            # 숫자 추출 시도
                            try:
                                # 콤마와 공백 제거
                                clean_value = str_value.replace(',', '').replace(' ', '')
                                
                                # 음수 처리
                                is_negative = clean_value.startswith('-')
                                if is_negative:
                                    clean_value = clean_value[1:]
                                
                                # 숫자인지 확인 (소수점 포함)
                                if clean_value.replace('.', '').isdigit():
                                    num_value = float(clean_value)
                                    int_value = int(num_value)
                                    
                                    # 음수 처리
                                    if is_negative:
                                        int_value = -int_value
                                    
                                    # 콤마 포맷팅
                                    if int_value >= 0:
                                        return f"{int_value:,}"
                                    else:
                                        return f"({abs(int_value):,})"  # 음수는 괄호로 표시
                                else:
                                    return str_value  # 숫자가 아니면 원본 그대로
                            except:
                                return str_value  # 변환 실패시 원본 그대로
                        
                        # 금액 컬럼들에 포맷팅 적용
                        for col in column_names[1:]:  # 계정과목 제외한 금액 컬럼들
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(format_amount)
                        
                        st.dataframe(display_df, use_container_width=True, height=400)
                        
                        # 데이터 정보 표시
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.info(f"📊 총 {len(display_df)}개 계정과목")
                        with col_info2:
                            if prev_amount_col:
                                st.info(f"✅ 전기 데이터 포함 ({prev_amount_col})")
                            else:
                                st.warning("⚠️ 전기 데이터 없음")
                    else:
                        st.dataframe(df_financial, use_container_width=True)
            else:
                # 자연스러운 안내 메시지
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                st.markdown("### 📅 재무제표 공시 안내")
                
                if analysis_year == current_year:
                    if report_code == '11011':  # 사업보고서
                        if current_month < 4:
                            st.info("""
                            📊 **사업보고서 공시 일정**
                            - 사업보고서는 통상 매년 **3월 말**에 공시됩니다
                            - 현재 아직 공시 시기가 되지 않았습니다
                            - 2024년도 데이터를 먼저 확인해보세요
                            """)
                        else:
                            st.warning("📋 사업보고서가 아직 공시되지 않았습니다.")
                    elif report_code == '11012':  # 반기보고서
                        if current_month < 9:
                            st.info("""
                            📊 **반기보고서 공시 일정**
                            - 반기보고서는 통상 매년 **8월 말**에 공시됩니다
                            - 현재 아직 공시 시기가 되지 않았습니다
                            """)
                        else:
                            st.warning("📋 반기보고서가 아직 공시되지 않았습니다.")
                    elif report_code == '11013':  # 1분기보고서
                        if current_month < 6:
                            st.info("""
                            📊 **1분기보고서 공시 일정**
                            - 1분기보고서는 통상 매년 **5월 말**에 공시됩니다
                            - 현재 아직 공시 시기가 되지 않았습니다
                            """)
                        else:
                            st.warning("📋 1분기보고서가 아직 공시되지 않았습니다.")
                    elif report_code == '11014':  # 3분기보고서
                        if current_month < 12:
                            st.info("""
                            📊 **3분기보고서 공시 일정**
                            - 3분기보고서는 통상 매년 **11월 말**에 공시됩니다
                            - 현재 아직 공시 시기가 되지 않았습니다
                            """)
                        else:
                            st.warning("📋 3분기보고서가 아직 공시되지 않았습니다.")
                else:
                    st.warning(f"📋 {analysis_year}년도 재무제표 데이터를 찾을 수 없습니다.")
                
                st.markdown("""
                ### 💡 **권장 사항**
                
                **📊 다른 연도 시도:**
                - 2024년 → 2023년 → 2022년 순으로 변경해보세요
                
                **📋 다른 보고서 유형:**
                - 사업보고서가 없다면 반기보고서나 분기보고서를 확인해보세요
                
                **🏢 기업 확인:**
                - 상장기업인지 확인 (비상장기업은 공시 의무가 제한적)
                - 기업명과 기업코드가 정확한지 확인
                """)
                
                # 현재 선택된 설정 표시
                report_type_name = {
                    '11011': '사업보고서',
                    '11012': '반기보고서', 
                    '11013': '1분기보고서',
                    '11014': '3분기보고서'
                }.get(report_code, '알 수 없음')
                
                st.info(f"📅 **현재 선택**: {analysis_year}년 {report_type_name}")
        
        # 탭 3: 시각화
        with tab3:
            st.markdown("### 📊 재무 데이터 시각화")
            
            if financial_data and financial_data.get('list'):
                df_financial = pd.DataFrame(financial_data['list'])
                metrics = extract_key_metrics(df_financial)
                
                if metrics:
                    # 당기 vs 전기 비교 (전기 데이터가 있는 경우)
                    prev_metrics = {k: v for k, v in metrics.items() if k.endswith('_전기')}
                    if prev_metrics:
                        st.markdown("#### 📈 당기 vs 전기 비교")
                        
                        # 비교 데이터 준비
                        comparison_data = []
                        for metric_name in ['매출액', '영업이익', '당기순이익']:
                            if metric_name in metrics and f"{metric_name}_전기" in metrics:
                                comparison_data.append({
                                    '항목': metric_name,
                                    '당기': metrics[metric_name] / 1e12,
                                    '전기': metrics[f"{metric_name}_전기"] / 1e12
                                })
                        
                        if comparison_data:
                            df_comparison = pd.DataFrame(comparison_data)
                            
                            # 막대 차트로 비교
                            fig = px.bar(
                                df_comparison.melt(id_vars=['항목'], var_name='기간', value_name='금액'),
                                x='항목', y='금액', color='기간',
                                title="당기 vs 전기 주요 지표 비교 (조원)",
                                labels={'금액': '금액 (조원)'},
                                barmode='group'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 증감률 계산 및 표시
                            growth_data = []
                            for item in comparison_data:
                                if item['전기'] != 0:
                                    growth_rate = ((item['당기'] - item['전기']) / item['전기']) * 100
                                    growth_data.append({
                                        '항목': item['항목'],
                                        '증감률': f"{growth_rate:+.1f}%"
                                    })
                            
                            if growth_data:
                                st.markdown("#### 📊 전년 대비 증감률")
                                cols = st.columns(len(growth_data))
                                for i, data in enumerate(growth_data):
                                    with cols[i]:
                                        growth_value = float(data['증감률'].replace('%', '').replace('+', ''))
                                        if growth_value > 0:
                                            st.metric(data['항목'], data['증감률'], delta=f"+{growth_value:.1f}%")
                                        else:
                                            st.metric(data['항목'], data['증감률'], delta=f"{growth_value:.1f}%")
                    
                    # 당기 매출 및 이익 차트
                    st.markdown("#### 💰 당기 매출 및 이익 현황")
                    profit_data = {k: v for k, v in metrics.items() if k in ['매출액', '영업이익', '당기순이익'] and not k.endswith('_전기')}
                    if profit_data:
                        fig = px.bar(
                            x=list(profit_data.keys()),
                            y=[v/1e12 for v in profit_data.values()],
                            title="매출 및 이익 현황 (조원)",
                            labels={'x': '항목', 'y': '금액 (조원)'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 재무상태 차트
                    st.markdown("#### 🏦 재무상태 구성")
                    balance_data = {k: v for k, v in metrics.items() if k in ['자산총계', '부채총계', '자본총계'] and not k.endswith('_전기')}
                    if balance_data:
                        fig = px.pie(
                            values=list(balance_data.values()),
                            names=list(balance_data.keys()),
                            title="재무상태표 구성"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("시각화할 데이터가 없습니다.")
        
        # 탭 4: 공시 정보
        with tab4:
            st.markdown("### 📑 최근 공시 정보")
            
            try:
                current_year = datetime.now().year
                bgn_date = f"{current_year-1}0101"  # 작년부터
                end_date = f"{current_year}1231"    # 올해까지
                
                url = f"{dart_api.base_url}/list.json"
                params = {
                    'crtfc_key': dart_api.api_key,
                    'corp_code': selected_corp_code,
                    'bgn_de': bgn_date,
                    'end_de': end_date,
                    'last_reprt_at': 'Y',
                    'pblntf_ty': 'A',
                    'page_no': '1',
                    'page_count': '20'
                }
                
                with st.spinner("공시 정보를 불러오는 중..."):
                    response = requests.get(url, params=params, timeout=15)
                    disclosure_data = response.json()
                
                if disclosure_data.get('status') == '000' and disclosure_data.get('list'):
                    df_disclosures = pd.DataFrame(disclosure_data['list'])
                    
                    # 주요 컬럼만 표시
                    display_columns = ['rcept_dt', 'corp_name', 'report_nm']
                    available_columns = [col for col in display_columns if col in df_disclosures.columns]
                    
                    if available_columns:
                        display_df = df_disclosures[available_columns].copy()
                        column_mapping = {
                            'rcept_dt': '접수일자',
                            'corp_name': '기업명', 
                            'report_nm': '보고서명'
                        }
                        display_df = display_df.rename(columns=column_mapping)
                        st.dataframe(display_df, use_container_width=True)
                    
                    # 공시 통계
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("총 공시 건수", len(df_disclosures))
                    with col2:
                        if 'report_nm' in df_disclosures.columns:
                            unique_reports = df_disclosures['report_nm'].nunique()
                            st.metric("보고서 종류", f"{unique_reports}개")
                    
                    st.info(f"📅 조회 기간: {current_year-1}년 ~ {current_year}년")
                else:
                    st.warning(f"공시 정보 조회 실패: {disclosure_data.get('message', '데이터 없음')}")
                    
            except Exception as e:
                st.error(f"공시 정보 조회 실패: {e}")
        
 # 탭 5: AI 분석
        with tab5:
            st.markdown(f"### ⚫ {selected_model} 분석창")
            
            auto_question_value = st.session_state.pop('auto_question', "")
            
            question_text = st.text_area(
                "분석할 질문을 입력하세요:",
                value=auto_question_value,
                placeholder=f"예시:\n• {selected_corp_name}의 최근 실적은 어떤가요?\n• {selected_corp_name}의 투자 리스크는?",
                height=120
            )
            
            if st.button("🚀 분석 실행"):
                # ▼ 변경/추가된 부분: 모델별 API 키 확인
                api_key_provided = False
                if selected_model == "GPT-4o" and openai_api_key:
                    api_key_provided = True
                elif selected_model == "Gemma 3 27b" and google_api_key:
                    api_key_provided = True

                if not api_key_provided:
                    st.error(f"🔑 {selected_model}을(를) 사용하려면 사이드바에서 해당 API 키를 입력해주세요!")
                # ▲ 변경/추가된 부분
                elif not question_text.strip():
                    st.error("❓ 질문을 입력해주세요!")
                else:
                    # 1) 재무 데이터 준비
                    financial_summary = ""
                    if financial_data and financial_data.get('list'):
                        df_financial = pd.DataFrame(financial_data['list'])
                        metrics = extract_key_metrics(df_financial)
                        ratios = calculate_financial_ratios(metrics)
                        
                        financial_summary = f"=== {selected_corp_name} {analysis_year}년 재무 데이터 ===\n\n주요 재무 지표:\n"
                        for metric, value in metrics.items():
                            if not metric.endswith('_전기'):
                                financial_summary += f"- {metric}: {value:,}원 ({value/1e12:.2f}조원)\n"
                        
                        if ratios:
                            financial_summary += "\n재무 비율:\n"
                            for ratio, value in ratios.items():
                                financial_summary += f"- {ratio}: {value:.2f}%\n"
                    else:
                        financial_summary = f"{selected_corp_name}의 {analysis_year}년 재무 데이터를 불러올 수 없습니다."
                    
                    # 2) 기업 정보 준비
                    company_summary = ""
                    if company_info and company_info.get('list'):
                        info = company_info['list'][0]
                        stock_code = info.get('stock_code', '')
                        company_summary = f"=== {selected_corp_name} 기업 정보 ===\n"
                        company_summary += f"- 기업명: {info.get('corp_name', 'N/A')}\n"
                        company_summary += f"- 기업코드: {info.get('corp_code', 'N/A')}\n"
                        company_summary += f"- 주식코드: {stock_code if stock_code else '비상장'}\n"
                        company_summary += f"- 분석연도: {analysis_year}년\n"
                    
                    # 3) 실시간 웹 검색 실행 (SerpAPI 사용) - 디버깅 강화
                    web_text = ""
                    if use_serpapi:
                        st.info("🔍 실시간 웹 검색 중...")
                        # 간단하고 효과적인 검색 쿼리 생성
                        search_query = f"{question_text}"
                        st.write(f"🔍 검색어: {search_query}")  # 디버깅용
                        
                        try:
                            web_text = search_serpapi(search_query, num=5)
                            if web_text and "검색 결과가 없습니다" not in web_text:
                                st.success(f"✅ 검색 완료: {len(web_text)}자의 최신 정보 수집")
                                # 검색 결과 미리보기
                                with st.expander("🔍 검색된 최신 정보 미리보기", expanded=False):
                                    st.markdown(web_text[:1000] + "..." if len(web_text) > 1000 else web_text)
                            else:
                                st.warning("⚠️ 관련 검색 결과를 찾지 못했습니다.")
                                web_text = "관련 검색 결과가 없습니다."
                        except Exception as e:
                            st.error(f"❌ 검색 오류: {e}")
                            web_text = "검색 중 오류가 발생했습니다."
                    else:
                        st.info("📋 웹 검색이 비활성화되어 재무 데이터만 사용합니다.")
                    
                    # 4) DB에서 추가 정보 수집 (사용자 요청 시)
                    db_info = ""
                    question_lower = question_text.lower()
                    db_keywords = ['저장된', 'db', '데이터베이스', '이전', '과거', '기록', '히스토리', '비교', '다른 기업']
                
                    if any(keyword in question_lower for keyword in db_keywords):
                        st.info("🔍 DB에서 관련 정보를 검색 중...")
                
                        # 저장된 기업 목록 조회
                        saved_companies = db.get_companies()
                        if not saved_companies.empty:
                            db_info += f"\n=== 💾 저장된 기업 데이터 ({len(saved_companies)}개) ===\n"
                            for _, company in saved_companies.iterrows():
                                stock_info = f" ({company['stock_code']})" if company['stock_code'] else ""
                                db_info += f"- {company['corp_name']}{stock_info}\n"
                        # 모든 기업의 재무 지표 조회 - 다양한 지표 포함
                        all_metrics = db.get_financial_metrics(limit=saved_companies.shape[0] or 15)
                        if not all_metrics.empty:
                            db_info += "\n=== 📊 전체 기업 주요 재무 지표 종합 ===\n"
                            
                            # 지표별로 그룹화하여 표시
                            db_info += "\n📈 **수익성 지표:**\n"
                            for _, metric in all_metrics.iterrows():
                                corp = metric['corp_name']
                                year = metric['year']
                                rep = metric['report_type']
                                
                                # 영업이익 (Operating Profit)
                                op_profit = (metric.get('operating_profit') or 0) / 1e12
                                # 순이익 (Net Income)
                                net_income = (metric.get('net_income') or 0) / 1e12
                                # 영업이익률 (Operating Margin)
                                op_margin = metric.get('operating_margin', 0)
                                # 순이익률 (Net Margin)  
                                net_margin = metric.get('net_margin', 0)
                                
                                if op_profit != 0 or net_income != 0:
                                    db_info += f"- {corp} {year}년: 영업이익 {op_profit:.1f}조원, 순이익 {net_income:.1f}조원"
                                    if op_margin > 0:
                                        db_info += f", 영업이익률 {op_margin:.1f}%"
                                    if net_margin > 0:
                                        db_info += f", 순이익률 {net_margin:.1f}%"
                                    db_info += "\n"
                            
                            db_info += "\n💪 **효율성 지표 (ROE, ROA):**\n"
                            for _, metric in all_metrics.iterrows():
                                corp = metric['corp_name']
                                year = metric['year']
                                roe = metric.get('roe', 0)
                                roa = metric.get('roa', 0)
                                
                                if roe > 0 or roa > 0:
                                    db_info += f"- {corp} {year}년: "
                                    if roe > 0:
                                        db_info += f"ROE {roe:.1f}%"
                                    if roa > 0:
                                        db_info += f", ROA {roa:.1f}%" if roe > 0 else f"ROA {roa:.1f}%"
                                    db_info += "\n"
                            
                            db_info += "\n🏦 **재무구조 지표:**\n"
                            for _, metric in all_metrics.iterrows():
                                corp = metric['corp_name']
                                year = metric['year']
                                # 자산총계
                                total_assets = (metric.get('total_assets') or 0) / 1e12
                                # 부채총계
                                total_liabilities = (metric.get('total_liabilities') or 0) / 1e12
                                # 자본총계
                                total_equity = (metric.get('total_equity') or 0) / 1e12
                                # 부채비율
                                debt_ratio = metric.get('debt_ratio', 0)
                                
                                if total_assets > 0:
                                    db_info += f"- {corp} {year}년: 자산 {total_assets:.1f}조원"
                                    if total_liabilities > 0:
                                        db_info += f", 부채 {total_liabilities:.1f}조원"
                                    if total_equity > 0:
                                        db_info += f", 자본 {total_equity:.1f}조원"
                                    if debt_ratio > 0:
                                        db_info += f", 부채비율 {debt_ratio:.1f}%"
                                    db_info += "\n"

                        
                        # GPT 분석 기록
                        gpt_history = db.get_gpt_analysis_history(selected_corp_code, limit=3)
                        if not gpt_history.empty:
                            db_info += f"\n=== 🤖 {selected_corp_name} 이전 분석 ===\n"
                            for _, record in gpt_history.iterrows():
                                question_short = record['question'][:50] + "..." if len(record['question']) > 50 else record['question']
                                db_info += f"- Q: {question_short}\n"
                        
                        if db_info:
                            st.success(f"✅ DB에서 관련 정보를 찾았습니다!")
                        else:
                            db_info = "관련된 저장된 데이터가 없습니다."
                    # 5) GPT 시스템 프롬프트 생성 (검색 결과 + DB 정보 포함)
                    system_prompt = f"""당신은 한국의 금융 분석 전문가입니다.
아래 기업의 재무 데이터, 최신 웹 검색 결과, 저장된 DB 정보를 종합하여 사용자 질문에 답변하세요.

=== 기업 정보 ===
{company_summary}

=== 재무 데이터 ===
{financial_summary}

=== ⚡ 최신 웹 검색 결과 (실시간 정보) ===
{web_text}
=== 검색 결과 끝 ===

=== 💾 저장된 DB 정보 ===
{db_info if db_info else "사용자가 DB 관련 질문을 하지 않아 DB 정보를 조회하지 않았습니다."}
=== DB 정보 끝 ===

💡 답변 가이드:
- 위의 재무 데이터, 최신 검색 결과, DB 정보를 모두 활용하세요
- 검색된 최신 정보를 적극적으로 반영하세요
- DB에 저장된 과거 데이터와 현재 데이터를 비교 분석하세요
- 구체적인 숫자와 근거를 제시하세요
- 투자자 관점에서 실용적인 조언을 제공하세요
- 긍정적/부정적 측면을 균형있게 분석하세요
- 한국어로 이해하기 쉽게 작성하세요"""

                    # 6) 메시지 구성: system + 과거 히스토리 + 이번 질문
                    messages = [
                        {"role": "system", "content": system_prompt}
                    ] + st.session_state.chat_history + [
                        {"role": "user", "content": question_text}
                    ]

                    # 7) 스피너 & 빈 컨테이너 준비
                    spinner = st.spinner("🤖 AI가 최신 정보를 반영하여 분석하는 중...")
                    container = st.empty()
                    answer = ""

                    # 8) 스트리밍 호출
                    try:
                        with spinner:
                            # ▼ 변경/추가된 부분: 선택된 모델에 따라 분기 처리
                            if selected_model == "GPT-4o":
                                client = OpenAI(api_key=openai_api_key)
                                messages = [{"role": "system", "content": system_prompt}] + st.session_state.chat_history + [{"role": "user", "content": question_text}]
                                

                            elif selected_model == "Gemma 3 27b":
                                genai.configure(api_key=google_api_key)
                                model = genai.GenerativeModel(
                                    'models/gemma-3-27b-it'
                                    # system_instruction 인자를 제거합니다.
                                )
                                # Gemini는 history를 직접 지원하므로 변환
                                # system_prompt를 첫 번째 메시지로 추가하거나 history에 포함하는 방식을 고려
                                if not st.session_state.chat_history: # 채팅 기록이 없으면
                                    # 시스템 프롬프트를 첫 사용자 메시지에 통합
                                    combined_question = f"{system_prompt}\n\n{question_text}"
                                    chat = model.start_chat(history=[]) # 초기에는 history를 비워둡니다.
                                    response = chat.send_message(combined_question, stream=True)
                                else:
                                    # 채팅 기록이 있으면 기존처럼 history를 사용
                                    formatted_history = convert_history_to_genai_format(st.session_state.chat_history)
                                    chat = model.start_chat(history=formatted_history)
                                    
                                    # [수정된 부분] 매번 새로운 시스템 프롬프트와 질문을 결합하여 전달
                                    combined_question = f"{system_prompt}\n\n{question_text}"
                                    response = chat.send_message(combined_question, stream=True)

                                # for chunk in response:
                                #     if chunk.text:
                                #         answer += chunk.text
                                #         container.markdown(answer)
#오류 메세지해결----------------------------------------------------------------
                                for chunk in response:
                                    try:
                                        # chunk.text가 없거나 비어있는 경우를 안전하게 처리
                                        if chunk.text:
                                            answer += chunk.text
                                            container.markdown(answer)
                                    except Exception as e:
                                        # 특정 오류(Invalid operation)를 포함하여 스트리밍 중 발생할 수 있는
                                        # 예상치 못한 오류를 캐치하고 건너뛸 수 있습니다.
                                        # print(f"Warning: Failed to process chunk.text: {e}") # 디버깅용
                                        pass # 텍스트가 없는 청크는 무시하고 다음 청크로 넘어갑니다.
#------------------------------------------------------------------------------

                        # 히스토리 저장 및 DB 저장
                        st.session_state.chat_history.append({"role": "user", "content": question_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

                        if save_to_db:
                            # ▼ 변경/추가된 부분: 저장 시 모델 이름도 함께 저장하면 좋지만, 현재 스키마에서는 생략
                            db.save_gpt_analysis(selected_corp_code, selected_corp_name, question_text, answer, use_serpapi)

                        st.markdown("---")
                        st.success(f"✅ {selected_model} 분석이 완료되었습니다!")
                        
                        # 추가 질문 제안
                        with st.expander("💡 추가 질문 제안", expanded=False):
                            suggestions = [
                                f"{selected_corp_name} 주가는 앞으로 어떻게 될까요?",
                                f"{selected_corp_name}의 가장 큰 리스크는 무엇인가요?",
                                f"{selected_corp_name}에 지금 투자해도 될까요?",
                                f"{selected_corp_name}과 경쟁사 중 어디가 더 좋나요?"
                            ]
                            
                            for i, suggestion in enumerate(suggestions):
                                if st.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
                                    st.session_state.auto_question = suggestion
                                    st.rerun()
                        
                        # 검색 결과 상세 보기
                        if web_text and "검색 결과가 없습니다" not in web_text:
                            with st.expander("📡 사용된 최신 검색 결과", expanded=False):
                                st.markdown("**🔍 AI 분석에 활용된 실시간 정보:**")
                                st.markdown(web_text)
                        
                    except Exception as e:
                        st.error(f"❌ AI 분석 중 오류가 발생했습니다: {e}")
            
            # 대화 히스토리 표시 및 관리
            if st.session_state.chat_history:
                st.markdown("### 💬 대화 기록")
                
                # 최근 3개 대화만 표시
                recent_history = st.session_state.chat_history[-6:]  # user + assistant 쌍이므로 6개 = 3쌍
                for i in range(0, len(recent_history), 2):
                    if i+1 < len(recent_history):
                        user_msg = recent_history[i]['content']
                        assistant_msg = recent_history[i+1]['content']
                        
                        st.markdown(f"**🙋‍♂️ Q:** {user_msg}")
                        st.markdown(f"**🤖 A:** {assistant_msg[:300]}..." if len(assistant_msg) > 300 else f"**🤖 A:** {assistant_msg}")
                        st.markdown("---")
                
                # 관리 버튼
                if st.button("🗑️ 대화 기록 초기화"):
                    st.session_state.chat_history = []
                    st.success("대화 기록이 초기화되었습니다.")
                    st.rerun()
        
        # 탭 6: DB 관리
        with tab6:
            st.markdown("### 💾 데이터베이스 관리")
            
            # DB 통계 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 DB 현황")
                stats = db.get_db_stats()
                if stats:
                    st.metric("저장된 기업", f"{stats.get('companies', 0)}개")
                    st.metric("재무 기록", f"{stats.get('financial_records', 0)}건")
                    st.metric("재무 지표", f"{stats.get('financial_metrics', 0)}건")
                    st.metric("GPT 분석", f"{stats.get('gpt_analysis', 0)}건")
                    st.metric("DB 크기", f"{stats.get('db_size', 0):.2f}MB")
            
            with col2:
                st.markdown("#### 🗂️ 저장된 기업 목록")
                saved_companies = db.get_companies()
                if not saved_companies.empty:
                    # 최신 10개 기업만 표시
                    display_companies = saved_companies.head(10)
                    for _, company in display_companies.iterrows():
                        stock_info = f" ({company['stock_code']})" if company['stock_code'] else ""
                        updated_at = company['updated_at'][:16]  # YYYY-MM-DD HH:MM 형식
                        st.write(f"🏢 **{company['corp_name']}**{stock_info}")
                        st.caption(f"업데이트: {updated_at}")
                    
                    if len(saved_companies) > 10:
                        st.info(f"... 외 {len(saved_companies)-10}개 기업 더 있음")
                else:
                    st.info("저장된 기업이 없습니다.")
            
            # 재무 지표 조회
            st.markdown("#### 📈 저장된 재무 지표")
            
            # 현재 기업의 재무 지표 조회
            if selected_corp_code:
                financial_metrics = db.get_financial_metrics(selected_corp_code, limit=5)
                if not financial_metrics.empty:
                    st.write(f"**{selected_corp_name}의 저장된 재무 지표:**")
                    
                    # 주요 컬럼만 표시
                    # 더 다양한 지표 표시 (매출액 제외)
                    display_cols = [
                        'year', 'report_type', 
                        'operating_profit', 'net_income',  # 매출액 제외, 이익 지표 추가
                        'total_assets', 'total_equity',    # 자산, 자본 지표
                        'operating_margin', 'net_margin',  # 마진 지표
                        'roe', 'roa', 'debt_ratio',       # 효율성, 안정성 지표
                        'created_at'
                    ]
                    available_cols = [col for col in display_cols if col in financial_metrics.columns]
                    
                    if available_cols:
                        display_df = financial_metrics[available_cols].copy()
                        
                        # 컬럼명 한글화 (더 다양한 지표)
                        column_mapping = {
                            'year': '연도',
                            'report_type': '보고서',
                            'operating_profit': '영업이익',
                            'net_income': '순이익',
                            'total_assets': '자산총계',
                            'total_equity': '자본총계',
                            'operating_margin': '영업이익률(%)',
                            'net_margin': '순이익률(%)',
                            'roe': 'ROE(%)',
                            'roa': 'ROA(%)',
                            'debt_ratio': '부채비율(%)',
                            'created_at': '저장일시'
                        }
                        
                        display_df = display_df.rename(columns=column_mapping)
                        
                        # 금액 단위를 조 단위로 변환하고 포맷팅
                        money_cols = ['영업이익', '순이익', '자산총계', '자본총계']
                        for col in money_cols:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(
                                    lambda x: f"{x/1e12:.2f}조" if pd.notna(x) and x != 0 else "0.00조"
                                )
                        
                        # 비율 소수점 정리
                        ratio_cols = ['ROE(%)', 'ROA(%)', '부채비율(%)']
                        for col in ratio_cols:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(
                                    lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"
                                )
                        
                        # 저장일시 간소화
                        if '저장일시' in display_df.columns:
                            display_df['저장일시'] = display_df['저장일시'].str[:16]
                        
                        st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("현재 기업의 저장된 재무 지표가 없습니다.")
            
            # 전체 재무 지표 (최신 10건)
            with st.expander("📊 전체 기업 재무 지표 (최신 10건)", expanded=False):
                all_metrics = db.get_financial_metrics(limit=10)
                if not all_metrics.empty:
                    # 매출액 대신 다른 지표들 포함
                    display_cols = [
                        'corp_name', 'year', 'report_type', 
                        'operating_profit', 'net_income',  # 수익성 지표
                        'roe', 'roa',                      # 효율성 지표  
                        'debt_ratio',                      # 안정성 지표
                        'created_at'
                    ]
                    available_cols = [col for col in display_cols if col in all_metrics.columns]
                    
                    if available_cols:
                        display_df = all_metrics[available_cols].copy()
                        column_mapping = {
                            'corp_name': '기업명',
                            'year': '연도',
                            'report_type': '보고서',
                            'operating_profit': '영업이익(조)',
                            'net_income': '순이익(조)',
                            'roe': 'ROE(%)',
                            'roa': 'ROA(%)',
                            'debt_ratio': '부채비율(%)',
                            'created_at': '저장일시'
                        }
                        display_df = display_df.rename(columns=column_mapping)
                        
                        # 이익 지표 단위 변환 (원 → 조원)
                        profit_cols = ['영업이익(조)', '순이익(조)']
                        for col in profit_cols:
                            if col in display_df.columns:
                                display_df[col] = (display_df[col] / 1e12).round(2)           
                        
                        # ROE 소수점 정리
                        if 'ROE(%)' in display_df.columns:
                            display_df['ROE(%)'] = display_df['ROE(%)'].round(2)
                        
                        # 저장일시 간소화
                        if '저장일시' in display_df.columns:
                            display_df['저장일시'] = display_df['저장일시'].str[:16]
                        
                        st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("저장된 재무 지표가 없습니다.")
            
            # GPT 분석 기록
            st.markdown("#### 🤖 GPT 분석 기록")
            
            # 현재 기업의 GPT 분석 기록
            if selected_corp_code:
                gpt_history = db.get_gpt_analysis_history(selected_corp_code, limit=3)
                if not gpt_history.empty:
                    st.write(f"**{selected_corp_name}의 GPT 분석 기록 (최신 3건):**")
                    
                    for _, record in gpt_history.iterrows():
                        with st.expander(f"🤖 {record['question'][:50]}... ({record['created_at'][:16]})", expanded=False):
                            st.markdown(f"**질문:** {record['question']}")
                            st.markdown(f"**답변:** {record['answer'][:500]}..." if len(record['answer']) > 500 else f"**답변:** {record['answer']}")
                            web_search_icon = "🌐" if record['used_web_search'] else "📋"
                            st.caption(f"{web_search_icon} 웹 검색 {'사용' if record['used_web_search'] else '미사용'}")
                else:
                    st.info("현재 기업의 GPT 분석 기록이 없습니다.")
            
            # 전체 GPT 분석 기록 (최신 5건)
            with st.expander("🤖 전체 GPT 분석 기록 (최신 5건)", expanded=False):
                all_gpt_history = db.get_gpt_analysis_history(limit=5)
                if not all_gpt_history.empty:
                    for _, record in all_gpt_history.iterrows():
                        st.markdown(f"**🏢 {record['corp_name']}** - {record['created_at'][:16]}")
                        st.markdown(f"**Q:** {record['question'][:100]}..." if len(record['question']) > 100 else f"**Q:** {record['question']}")
                        web_search_icon = "🌐" if record['used_web_search'] else "📋"
                        st.caption(f"{web_search_icon} 웹 검색 {'사용' if record['used_web_search'] else '미사용'}")
                        st.markdown("---")
                else:
                    st.info("저장된 GPT 분석 기록이 없습니다.")
            
            # DB 관리 기능
            st.markdown("#### 🗂️ DB 관리 기능")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 DB 백업", help="현재 DB를 백업합니다"):
                    try:
                        backup_path = f"dart_analysis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                        import shutil
                        shutil.copy2(db.db_path, backup_path)
                        st.success(f"✅ DB 백업 완료: {backup_path}")
                    except Exception as e:
                        st.error(f"❌ DB 백업 실패: {e}")
            
            with col2:
                if st.button("📊 DB 최적화", help="DB 성능을 최적화합니다"):
                    try:
                        conn = sqlite3.connect(db.db_path, check_same_thread=False)
                        conn.execute("VACUUM")
                        conn.close()
                        st.success("✅ DB 최적화 완료")
                    except Exception as e:
                        st.error(f"❌ DB 최적화 실패: {e}")
            
            with col3:
                if st.button("🗑️ 전체 삭제", help="⚠️ 모든 데이터를 삭제합니다", type="secondary"):
                    if st.checkbox("정말로 모든 데이터를 삭제하시겠습니까?"):
                        try:
                            conn = sqlite3.connect(db.db_path, check_same_thread=False)
                            cursor = conn.cursor()
                            
                            # 모든 테이블 데이터 삭제
                            cursor.execute("DELETE FROM companies")
                            cursor.execute("DELETE FROM financial_data")
                            cursor.execute("DELETE FROM financial_metrics")
                            cursor.execute("DELETE FROM gpt_analysis")
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ 모든 데이터가 삭제되었습니다")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 데이터 삭제 실패: {e}")
           # ⭐⭐⭐ 여기부터 새로 추가되는 부분 ⭐⭐⭐
            
            # 데이터 백업 & 복원 기능 추가
            st.markdown("#### 📤 데이터 백업 & 복원")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📤 데이터 내보내기**")
                if st.button("💾 DB를 JSON으로 백업"):
                    backup_data = db.export_db_json()
                    if backup_data:
                        import json
                        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
                        
                        st.download_button(
                            label="📥 백업 파일 다운로드",
                            data=backup_json,
                            file_name=f"dart_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success("✅ 백업 파일이 준비되었습니다!")
            
            with col2:
                st.markdown("**📥 데이터 가져오기**")
                uploaded_file = st.file_uploader(
                    "백업 JSON 파일 업로드", 
                    type=['json'],
                    help="이전에 백업한 JSON 파일을 업로드하여 데이터를 복원하세요"
                )
                
                if uploaded_file is not None:
                    try:
                        import json
                        backup_data = json.load(uploaded_file)
                        
                        if st.button("🔄 데이터 복원"):
                            if db.import_db_json(backup_data):
                                st.success("✅ 데이터가 성공적으로 복원되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 데이터 복원에 실패했습니다.")
                                
                        # 백업 파일 내용 미리보기
                        with st.expander("📋 백업 파일 내용 미리보기"):
                            for table, data in backup_data.items():
                                st.write(f"**{table}**: {len(data)}건")
                                
                    except Exception as e:
                        st.error(f"❌ 파일 읽기 실패: {e}")
            
            # 세션 기반 DB 안내
            st.markdown("#### ⚠️ 배포 환경 DB 안내")
            st.info("""
            **📋 배포 환경 DB 특징:**
            - 세션 기반: 브라우저 세션이 유지되는 동안 데이터 보관
            - 임시 저장: 앱 재시작 시 데이터 초기화됨
            - 백업 권장: 중요한 분석 결과는 JSON으로 백업하세요
            
            **💡 사용 팁:**
            - 분석 후 바로 백업 파일 다운로드
            - 다음 사용 시 백업 파일 업로드하여 데이터 복원
            """)
            
            # ⭐⭐⭐ 여기까지 새로 추가되는 부분 ⭐⭐⭐                  
    
    else:
        st.info("좌측 사이드바에서 기업을 선택해주세요.")
        
        # 사용 가이드 - DB 기능 추가
        st.markdown("""
        ### 🎯 사용 가이드
        
        #### 📊 **기업 검색 방법**
        1. **기업명 검색**: 삼성전자, LG전자 등 기업명으로 검색
        2. **DART API**: 실시간 최신 데이터 조회
        3. **자동 저장**: 분석한 데이터 자동 DB 저장 (설정 시)
        
        #### 💾 **데이터베이스 기능**
        - **자동 저장**: "📀 분석 데이터 DB 저장" 체크 시 자동 저장
        - **스마트 활용**: GPT가 DB 키워드 감지 시 자동으로 저장된 데이터 활용
        - **분석 기록**: 모든 GPT 분석 결과 자동 저장
        - **DB 관리**: 백업, 최적화, 삭제 등 관리 기능 이전에 분석한 기업의 저장된 데이터 빠른 조회
        - **자동 저장**: 기업정보, 재무데이터, GPT 분석 결과 자동 저장
        - **분석 기록**: GPT 분석 질문과 답변 히스토리 보관
        - **DB 관리**: 백업, 최적화, 삭제 등 관리 기능
        
        #### 🔧 **주요 기업 코드**
        ```
        삼성전자: 00126380     SK하이닉스: 00164779
        LG전자: 00401731       현대자동차: 00164742
        NAVER: 00293886        포스코홀딩스: 00434003
        ```
        
        #### 📋 **제공되는 정보**
        - **기업 정보**: 기업명, 기업코드, 주식코드
        - **재무 분석**: 매출액, 영업이익, 자산, 부채 등 재무제표
        - **시각화**: 재무 데이터 차트 및 그래프
        - **공시 정보**: 최근 공시 현황 및 통계
        - **🤖 GPT 분석**: AI 기반 재무제표 분석 및 투자 인사이트
        - **💾 DB 관리**: 분석 데이터 저장 및 관리
        
        #### ⚡ **분석 팁**
        - **최신 데이터**: 2025년, 2024년 데이터 우선 확인
        - **분기별 비교**: 1분기, 3분기, 반기보고서 활용
        - **연도별 트렌드**: 여러 연도 데이터 비교 분석
        - **데이터 저장**: 분석한 기업은 DB에 저장되어 재활용 가능
        - **🤖 GPT 분석**: OpenAI API 키 입력 후 AI 기반 심층 분석 이용
        
        #### 🤖 **GPT 분석 기능**
        - **자유로운 질문**: 어떤 주제든 제약 없이 질문 가능
        - **자동 웹 검색**: 질문 내용에 맞는 최신 정보 자동 검색
        - **💾 스마트 DB 활용**: 특정 키워드 감지 시 저장된 데이터 자동 활용
          - "저장된", "DB", "이전", "과거", "기록", "비교", "다른 기업" 등
        - **종합 분석**: 실시간 데이터 + 웹 검색 + DB 정보 통합 분석
        - **분석 저장**: 모든 GPT 분석 결과가 DB에 자동 저장
        
        #### 💾 **DB 키워드 예시**
        - "저장된 다른 기업과 비교해주세요"
        - "이전 분석 기록을 보여주세요"
        - "DB에 있는 삼성전자 데이터와 비교"
        - "과거 재무 지표 변화 추이는?"
        
        #### 💾 **DB 관리 기능**
        - **자동 저장**: 기업 선택 시 "📀 분석 데이터 DB 저장" 체크 시 자동 저장
        - **저장 내용**: 기업정보, 재무데이터, 재무지표, GPT 분석 결과
        - **스마트 조회**: GPT가 필요 시 저장된 데이터 자동 검색
        - **분석 히스토리**: 이전 GPT 분석 질문/답변 기록 조회
        - **DB 관리**: 백업, 최적화, 전체 삭제 등 관리 기능
        """)
    
    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>📊 <strong>DART 실시간 기업분석 대시보드 + GPT 분석 + 💾 SQLite DB</strong></p>
            <p>데이터 출처: <a href="https://opendart.fss.or.kr" target="_blank">금융감독원 전자공시시스템 (DART)</a></p>
            <p>🤖 AI 분석: OpenAI GPT-4 | 📡 실시간 검색: SerpAPI | 💾 데이터 저장: SQLite3</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
