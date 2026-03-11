import sqlite3
import pandas as pd
import os

def get_db_connection():
    """데이터베이스 연결 객체 생성 (배포 환경 호환 경로)"""
    # src/utils.py 기준으로 ../data/nemostore.db 경로 탐색
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/nemostore.db'))
    return sqlite3.connect(db_path)

def load_data():
    """전체 데이터 로드 및 전처리"""
    conn = get_db_connection()
    query = "SELECT * FROM items"
    df = pd.read_sql(query, conn)
    conn.close()
    
    # 데이터 전처리
    # 1. 면적 변환 (m2 -> 평)
    if 'size' in df.columns:
        df['size_pyung'] = (df['size'] / 3.3057).round(1)
    
    # 2. 평당 월세 계산 (가성비 지표)
    if 'monthlyRent' in df.columns and 'size_pyung' in df.columns:
        # 0으로 나누기 방지
        df['price_per_pyung'] = (df['monthlyRent'] / df['size_pyung'].replace(0, pd.NA)).astype(float).round(1)
    
    # 3. 지하철역 정보 추출 및 정제
    if 'nearSubwayStation' in df.columns:
        df['subway_name'] = df['nearSubwayStation'].str.split('(').str[0].str.strip()
        
    # 4. 지도 시각화를 위한 가상 좌표 (데이터에 좌표가 없으므로 지하철역 기준 랜덤 지터 적용)
    # 실제 서비스라면 Geocoding API를 사용해야 함
    # 여기서는 서울 중심부(공덕역 인근)를 기준으로 랜덤하게 배치하여 대시보드 기능을 시연
    import numpy as np
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
