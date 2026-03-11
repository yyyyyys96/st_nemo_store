import pandas as pd
import os
import numpy as np
import streamlit as st

def load_data():
    """전체 데이터 로드 및 전처리 (CSV 전용 버전)"""
    # 1. 파일 경로 설정 (이미지 구조: 루트/data/raw/real_estate_test.csv)
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'raw', 'real_estate_test.csv') 
    
    # 파일이 없는 경우를 대비
    if not os.path.exists(file_path):
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame()

    # 2. 중요: SQL 대신 read_csv를 사용합니다.
    # (기존 에러 'file is not a database'를 해결하는 핵심 코드)
    df = pd.read_csv(file_path)
    
    # --- 데이터 전처리 (dashboard.py 호환용) ---
    
    # 1. 면적 변환 (m2 -> 평)
    if 'size' in df.columns:
        df['size_pyung'] = (df['size'] / 3.3057).round(1)
    
    # 2. 평당 월세 계산 (가성비 지표)
    if 'monthlyRent' in df.columns and 'size_pyung' in df.columns:
        # 0으로 나누기 방지
        df['price_per_pyung'] = (df['monthlyRent'] / df['size_pyung'].replace(0, np.nan)).astype(float).round(1)
    
    # 3. 지하철역 정보 정제
    if 'nearSubwayStation' in df.columns:
        df['subway_name'] = df['nearSubwayStation'].str.split('(').str[0].str.strip()
        
    # 4. 지도 시각화를 위한 가상 좌표 (데이터에 lat, lon이 없을 경우 생성)
    if 'lat' not in df.columns or 'lon' not in df.columns:
        df['lat'] = 37.543 + np.random.uniform(-0.02, 0.02, len(df))
        df['lon'] = 126.951 + np.random.uniform(-0.02, 0.02, len(df))
    
    return df

def convert_df_to_csv(df):
    """DataFrame을 CSV로 변환 (다운로드용)"""
    return df.to_csv(index=False).encode('utf-8-sig')

def format_price(value):
    """가격을 읽기 쉬운 포맷으로 변경 (예: 1억 2000만)"""
    if pd.isna(value) or value == 0:
        return "0"
    
    value = int(value)
    if value >= 10000:
        억 = value // 10000
        만 = value % 10000
        if 만 == 0:
            return f"{억}억"
        return f"{억}억 {만}만"
    else:
        return f"{value}만"
