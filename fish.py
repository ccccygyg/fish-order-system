import streamlit as st
import pandas as pd
from datetime import datetime

# 設定網頁標題
st.set_page_config(page_title="魚貨訂單系統", layout="wide")
st.title("🐟 興旺魚貨網頁訂單系統")

# 1. 初始化資料 (使用 Session State 確保重新整理時資料不會消失)
if 'inventory' not in st.session_state:
    st.session_state.inventory = {
        "白鯧": {"單價": 500, "庫存": 10},
        "鮭魚切片": {"單價": 250, "庫存": 20},
        "大草蝦": {"單價": 400, "庫存": 15},
        "透抽": {"單價": 180, "庫存": 30},
        "龍虎斑": {"單價": 600, "庫存": 5}
    }

if 'orders' not in st.session_state:
    st.session_state.orders = []

# --- 側邊欄：現貨狀態 ---
st.sidebar.header("📦 目前庫存清單")
df_inv = pd.DataFrame.from_dict(st.session_state.inventory, orient='index')
st.sidebar.table(df_inv)

# --- 主要區域：下單功能 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛒 新增訂單")
    with st.form("order_form", clear_on_submit=True):
        customer = st.text_input("客戶姓名")
        item = st.selectbox("選擇魚貨", list(st.session_state.inventory.keys()))
        qty = st.number_input("數量", min_value=1, step=1)
        
        submitted = st.form_submit_button("送出訂單")
        
        if submitted:
            stock = st.session_state.inventory[item]["庫存"]
            if qty > stock:
                st.error(f"❌ 庫存不足！目前僅剩 {stock}")
            else:
                # 扣庫存
                st.session_state.inventory[item]["庫存"] -= qty
                # 紀錄訂單
                price = st.session_state.inventory[item]["單價"]
                new_order = {
                    "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "客戶": customer,
                    "品項": item,
                    "數量": qty,
                    "總金額": price * qty
                }
                st.session_state.orders.append(new_order)
                st.success(f"✅ {customer} 的訂單已記錄！")
                st.rerun()

with col2:
    st.subheader("📋 訂單紀錄")
    if st.session_state.orders:
        df_orders = pd.DataFrame(st.session_state.orders)
        st.dataframe(df_orders, use_container_width=True)
        
        # 簡易統計
        total_sales = sum(o['總金額'] for o in st.session_state.orders)
        st.metric("今日總營業額", f"${total_sales}")
    else:
        st.write("目前尚無訂單")

# 重新開始按鈕
if st.button("清除所有資料重來"):
    st.session_state.clear()
    st.rerun()