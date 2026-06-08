import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# ส่วนที่ 1: การตั้งค่าฐานข้อมูล
# ==========================================
DB_NAME = 'suansamrian_farm.db'

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def fetch_data(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Planting_Cycles
                     (Cycle_ID TEXT PRIMARY KEY, Zone_ID TEXT, Plant_Date DATE, Est_Harvest_Date DATE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Tasks
                     (Task_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Task_Name TEXT, Due_Date DATE, Status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Expenses
                     (Exp_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Date DATE, Category TEXT, Amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Revenues
                     (Rev_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Date DATE, Quantity REAL, Amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Sensor_Logs
                     (Log_ID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp DATETIME, Sensor_Type TEXT, Value REAL)''')
        
        # [เพิ่มใหม่] ตารางบันทึกตารางรดน้ำและใส่ปุ๋ยรายวัน
        c.execute('''CREATE TABLE IF NOT EXISTS Daily_Schedules
                     (Sched_ID INTEGER PRIMARY KEY AUTOINCREMENT, Date DATE, Time TEXT, Zone_ID TEXT, Activity_Type TEXT, Detail TEXT, Status TEXT)''')
        conn.commit()

init_db()

# ==========================================
# ส่วนหน้าจอแอปพลิเคชัน (Frontend & UI)
# ==========================================
st.set_page_config(page_title="Smart Farm Manager", layout="wide")
st.title("🌱 Smart Farm Manager - สวนบุญเสถียรประภาชัย")

st.sidebar.header("เมนูหลัก")
menu = ["1. จัดการการปลูก (Crop)", "2. ตารางงานและการแจ้งเตือน (Tasks)", "3. บัญชี (Finance)", "4. ข้อมูลเซ็นเซอร์ (IoT)", "5. จัดการข้อมูล (Edit Data)"]
choice = st.sidebar.radio("เลือกโมดูลการทำงาน:", menu)

# --- โมดูลที่ 1: จัดการการปลูก (Crop) ---
if choice == "1. จัดการการปลูก (Crop)":
    st.header("📋 โมดูลจัดการรอบการปลูก (Crop Management)")
    df_cycles = fetch_data("SELECT * FROM Planting_Cycles ORDER BY Plant_Date DESC")
    tab_view, tab_add, tab_edit = st.tabs(["📊 ข้อมูลรอบการปลูกทั้งหมด", "➕ เพิ่มรอบการปลูกใหม่", "✏️ แก้ไขข้อมูลรอบการปลูก"])
    
    with tab_view:
        st.subheader("ตารางแสดงรอบการปลูกปัจจุบัน")
        if not df_cycles.empty: st.dataframe(df_cycles, use_container_width=True)
        else: st.info("ยังไม่มีข้อมูลรอบการปลูกในระบบ")

    with tab_add:
        with st.form("add_cycle_form"):
            st.subheader("กรอกรายละเอียดการปลูก")
            col1, col2 = st.columns(2)
            cycle_id = col1.text_input("รหัสรอบการปลูก (เช่น CYC-001)").strip()
            zone_id = col2.selectbox("เลือกล็อคแปลง", ["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"])
            plant_date = st.date_input("วันที่ลงหัวพันธุ์")
            submitted = st.form_submit_button("บันทึกข้อมูล")
            if submitted:
                if not cycle_id: st.error("⚠️ กรุณากรอกรหัสรอบการปลูกก่อนบันทึก")
                else:
                    est_harvest = plant_date + timedelta(days=45)
                    try:
                        run_query("INSERT INTO Planting_Cycles (Cycle_ID, Zone_ID, Plant_Date, Est_Harvest_Date) VALUES (?, ?, ?, ?)", (cycle_id, zone_id, plant_date, est_harvest))
                        st.success(f"✅ บันทึกรอบปลูก {cycle_id} สำเร็จ!")
                        st.rerun()
                    except sqlite3.IntegrityError: st.error("⚠️ รหัสรอบการปลูกนี้มีอยู่แล้วในระบบ")

    with tab_edit:
        st.subheader("แก้ไขรายละเอียดรอบการปลูก")
        if not df_cycles.empty:
            selected_edit_id = st.selectbox("เลือกรหัสรอบการปลูกที่ต้องการแก้ไขข้อมูล:", df_cycles['Cycle_ID'].tolist())
            row_data = df_cycles[df_cycles['Cycle_ID'] == selected_edit_id].iloc[0]
            with st.form("edit_cycle_form"):
                col1, col2 = st.columns(2)
                new_zone = col1.selectbox("เปลี่ยนล็อคแปลง", ["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"], index=["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"].index(row_data['Zone_ID']))
                new_plant_date = st.date_input("แก้ไขวันที่ลงหัวพันธุ์", value=pd.to_datetime(row_data['Plant_Date']).date())
                new_est_harvest = st.date_input("แก้ไขวันคาดการณ์เก็บเกี่ยว", value=pd.to_datetime(row_data['Est_Harvest_Date']).date())
                if st.form_submit_button("💾 อัปเดตเปลี่ยนแปลงข้อมูล"):
                    run_query("UPDATE Planting_Cycles SET Zone_ID = ?, Plant_Date = ?, Est_Harvest_Date = ? WHERE Cycle_ID = ?", (new_zone, new_plant_date, new_est_harvest, selected_edit_id))
                    st.success(f"✏️ อัปเดตข้อมูลรอบปลูก {selected_edit_id} เรียบร้อยแล้ว!"); st.rerun()
        else: st.info("ไม่มีข้อมูลสำหรับการแก้ไข")

# --- [ปรับปรุงใหญ่] โมดูลที่ 2: ตารางงานและการแจ้งเตือน ---
elif choice == "2. ตารางงานและการแจ้งเตือน (Tasks)":
    st.header("⏰ ระบบตารางงานและการแจ้งเตือนรายวัน")
    
    tab_today, tab_plan, tab_cycle_task = st.tabs(["🚨 ตารางงานวันนี้และการแจ้งเตือน", "📅 วางแผนรดน้ำ/ใส่ปุ๋ยรายวัน", "📦 งานตามรอบการปลูก"])
    
    today_date = datetime.now().date()
    
    # แท็บที่ 1: ตารางงานวันนี้และการแจ้งเตือน (ดึงงานที่ตรงกับวันปัจจุบันขึ้นมาโชว์)
    with tab_today:
        st.subheader(f"📅 รายการกิจกรรมประจำวันที่ {today_date.strftime('%d/%m/%Y')}")
        
        # ดึงข้อมูลงานของวันนี้ทั้งหมด
        df_today = fetch_data("SELECT * FROM Daily_Schedules WHERE Date = ? ORDER BY Time ASC", (today_date,))
        
        if not df_today.empty:
            # ส่วนแสดงกล่องแจ้งเตือนสรุปงานวันนี้ (Alert Dashboard)
            pending_count = len(df_today[df_today['Status'] == 'รอดำเนินการ'])
            if pending_count > 0:
                st.error(f"🚨 แจ้งเตือน: วันนี้มีงานรดน้ำ/ใส่ปุ๋ยที่ **รอดำเนินการอีก {pending_count} งาน** กรุณาตรวจสอบรายละเอียดด้านล่าง")
            else:
                st.success("🎉 ยอดเยี่ยม! วันนี้คุณทำภารกิจดูแลรดน้ำใส่ปุ๋ยครบถ้วน 100% แล้ว")
                
            st.markdown("---")
            
            # วาดการ์ดแสดงงานแต่ละชิ้นเพื่อให้ดูง่ายบนมือถือ
            for idx, row in df_today.iterrows():
                with st.container():
                    col_time, col_info, col_btn = st.columns([1, 3, 1])
                    
                    # คอลัมน์เวลาและประเภทงาน
                    col_time.markdown(f"### 🕒 {row['Time']}")
                    if row['Activity_Type'] == "💦 รดน้ำ":
                        col_time.caption("🔵 ระบบรดน้ำ")
                    else:
                        col_time.caption("🟠 ระบบให้ปุ๋ย")
                        
                    # คอลัมน์รายละเอียดงาน
                    col_info.markdown(f"**ตำแหน่ง:** {row['Zone_ID']} | **ประเภท:** {row['Activity_Type']}")
                    col_info.write(f"📝 รายละเอียด: {row['Detail']}")
                    
                    # คอลัมน์ปุ่มกดเปลี่ยนสถานะ
                    if row['Status'] == 'รอดำเนินการ':
                        col_btn.warning("⏳ รอดำเนินการ")
                        if col_btn.button("✅ ทำเสร็จแล้ว", key=f"daily_{row['Sched_ID']}"):
                            run_query("UPDATE Daily_Schedules SET Status = 'เสร็จแล้ว' WHERE Sched_ID = ?", (row['Sched_ID'],))
                            st.success("บันทึกสถานะสำเร็จ!")
                            st.rerun()
                    else:
                        col_btn.success("🟢 เสร็จสิ้น")
                    st.markdown("---")
        else:
            st.info("📅 วันนี้ไม่มีตารางรดน้ำหรือใส่ปุ๋ยที่ตั้งไว้ คุณสามารถไปเพิ่มแผนงานได้ที่แท็บ 'วางแผนรดน้ำ/ใส่ปุ๋ยรายวัน'")

    # แท็บที่ 2: ฟอร์มสร้างแผนงานรดน้ำ/ใส่ปุ๋ยรายวัน
    with tab_plan:
        st.subheader("➕ เพิ่มตารางแผนงานรดน้ำ / ใส่ปุ๋ยรายวัน")
        with st.form("add_daily_sched_form"):
            col1, col2, col3 = st.columns(3)
            sched_date = col1.date_input("วันที่ต้องการสั่งงาน", value=today_date)
            sched_time = col2.text_input("เวลา (เช่น 07:30, 16:00)", value="08:00").strip()
            sched_zone = col3.selectbox("เลือกโซนแปลงพืช", ["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"])
            
            col4, col5 = st.columns([1, 2])
            act_type = col4.radio("ประเภทกิจกรรม", ["💦 รดน้ำ", "🧪 ใส่ปุ๋ย"])
            sched_detail = col5.text_area("รายละเอียดสูตรปุ๋ย / ปริมาณน้ำ (เช่น ใส่ปุ๋ยสูตร 15-15-15 จำนวน 50 กรัม หรือ เปิดน้ำ 15 นาที)")
            
            if st.form_submit_button("💾 บันทึกเข้าตารางงานรายวัน"):
                if not sched_time or not sched_detail:
                    st.error("⚠️ กรุณากรอกข้อมูลเวลาและรายละเอียดงานให้ครบถ้วน")
                else:
                    run_query("INSERT INTO Daily_Schedules (Date, Time, Zone_ID, Activity_Type, Detail, Status) VALUES (?, ?, ?, ?, ?, 'รอดำเนินการ')",
                              (sched_date, sched_time, sched_zone, act_type, sched_detail))
                    st.success("✅ เพิ่มตารางแผนงานเรียบร้อยแล้ว!")
                    st.rerun()
                    
        # แสดงตารางแผนงานทั้งหมดในระบบให้เห็นด้านล่างฟอร์ม
        st.markdown("---")
        st.subheader("📋 แผนงานทั้งหมดในระบบ")
        df_all_sched = fetch_data("SELECT * FROM Daily_Schedules ORDER BY Date DESC, Time ASC")
        if not df_all_sched.empty:
            st.dataframe(df_all_sched, use_container_width=True)

    # แท็บที่ 3: งานตามรอบการปลูกเดิม (ฉีดพ่นไตรโคเดอร์มา)
    with tab_cycle_task:
        st.subheader("📦 ตารางงานบำรุงรักษาตามรอบปฏิทินการปลูก")
        df_all_cycles = fetch_data("SELECT Cycle_ID FROM Planting_Cycles ORDER BY Plant_Date DESC")
        if not df_all_cycles.empty:
            selected_cycle = st.selectbox("เลือกรอบการปลูกเพื่อดูตารางงาน", df_all_cycles['Cycle_ID'].tolist())
            df_tasks = fetch_data("SELECT * FROM Tasks WHERE Cycle_ID = ? ORDER BY Due_Date", (selected_cycle,))
            if not df_tasks.empty:
                for index, row in df_tasks.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"📝 **{row['Task_Name']}** (ครบกำหนด: {row['Due_Date']})")
                    if row['Status'] == 'รอดำเนินการ':
                        col2.warning("รอดำเนินการ")
                        if col3.button("✅ ทำเสร็จแล้ว", key=f"btn_{row['Task_ID']}"):
                            run_query("UPDATE Tasks SET Status = 'เสร็จแล้ว' WHERE Task_ID = ?", (row['Task_ID'],))
                            st.rerun()
                    else: col2.success("เสร็จสิ้นแล้ว")
            else: st.info("ไม่มีงานสำหรับรอบการปลูกนี้")
        else: st.warning("ยังไม่มีข้อมูลรอบการปลูกในระบบ")

# --- โมดูลที่ 3: บัญชี (Finance) ---
elif choice == "3. บัญชี (Finance)":
    st.header("💰 บัญชีและวิเคราะห์การเงิน")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("expense_form"):
            st.subheader("🔴 บันทึกรายจ่าย")
            e_cycle = st.text_input("รหัสรอบปลูก").strip()
            e_cat = st.selectbox("หมวดหมู่", ["ค่าหัวพันธุ์", "ค่าปุ๋ย/ยา", "ค่าแรง", "ค่าน้ำมัน"])
            e_date = st.date_input("วันที่เกิดรายการ (รายจ่าย)")
            e_amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
            if st.form_submit_button("บันทึกรายจ่าย") and e_cycle and e_amount > 0:
                run_query("INSERT INTO Expenses (Cycle_ID, Date, Category, Amount) VALUES (?, ?, ?, ?)", (e_cycle, e_date, e_cat, e_amount))
                st.success("✅ บันทึกรายจ่ายสำเร็จ!")
    with col2:
        with st.form("revenue_form"):
            st.subheader("🟢 บันทึกรายรับ")
            r_cycle = st.text_input("รหัสรอบปลูกที่ขาย").strip()
            r_date = st.date_input("วันที่เกิดรายการ (รายรับ)")
            r_qty = st.number_input("น้ำหนักผลผลิต (กก.)", min_value=0.0)
            r_amount = st.number_input("ยอดเงินรวม (บาท)", min_value=0.0)
            if st.form_submit_button("บันทึกรายรับ") and r_cycle and r_amount > 0:
                run_query("INSERT INTO Revenues (Cycle_ID, Date, Quantity, Amount) VALUES (?, ?, ?, ?)", (r_cycle, r_date, r_qty, r_amount))
                st.success("✅ บันทึกรายรับสำเร็จ!")
    st.markdown("---")
    df_exp = fetch_data("SELECT SUM(Amount) as Total_Exp FROM Expenses")
    df_rev = fetch_data("SELECT SUM(Amount) as Total_Rev FROM Revenues")
    tot_exp = df_exp['Total_Exp'][0] if pd.notnull(df_exp['Total_Exp'][0]) else 0.0
    tot_rev = df_rev['Total_Rev'][0] if pd.notnull(df_rev['Total_Rev'][0]) else 0.0
    st.columns(3)[0].metric("รายรับรวม", f"฿ {tot_rev:,.2f}")
    st.columns(3)[1].metric("รายจ่ายรวม", f"฿ {tot_exp:,.2f}")
    st.columns(3)[2].metric("กำไรสุทธิ", f"฿ {(tot_rev - tot_exp):,.2f}", delta=(tot_rev - tot_exp))

# --- โมดูลที่ 4: ข้อมูลเซ็นเซอร์ (IoT) ---
elif choice == "4. ข้อมูลเซ็นเซอร์ (IoT)":
    st.header("📡 ศูนย์รวบรวมข้อมูลเซ็นเซอร์แปลงและบ่อเลี้ยง")
    with st.expander("🛠️ จำลองการส่งค่าจากฮาร์ดแวร์เซ็นเซอร์ (Wi-Fi)"):
        col1, col2, col3 = st.columns(3)
        sim_target = col1.selectbox("เลือกประเภทระบบ", ["ระบบดิน (Soil)", "ระบบน้ำ (Water)"])
        if sim_target == "ระบบดิน (Soil)":
            sensor_type = col2.selectbox("เลือกเซ็นเซอร์ดิน", ["ความชื้นในดิน (%)", "pH ของดิน", "ค่าปุ๋ยไนโตรเจน (N)"])
            sim_val = col3.number_input("ค่าที่วัดได้", min_value=0.0, max_value=100.0, value=50.0)
        else:
            sensor_type = col2.selectbox("เลือกเซ็นเซอร์น้ำ", ["pH ของน้ำ", "ออกซิเจนละลายน้ำ (DO)", "อุณหภูมิน้ำ (°C)"])
            sim_val = col3.number_input("ค่าที่วัดได้", min_value=0.0, max_value=50.0, value=7.0)
        if st.button("🚀 ส่งค่าเข้าฐานข้อมูลระบบ"):
            run_query("INSERT INTO Sensor_Logs (Timestamp, Sensor_Type, Value) VALUES (DATETIME('now', 'localtime'), ?, ?)", (sensor_type, sim_val))
            st.success(f"บันทึกค่า {sensor_type} = {sim_val} สำเร็จ!"); st.rerun()

    st.markdown("---")
    tab_soil, tab_water = st.tabs(["🌱 ระบบตรวจวัดค่าดิน", "🐟 ระบบตรวจวัดค่าน้ำ"])
    with tab_soil:
        soil_sensor = st.selectbox("เลือกดูประวัติเซ็นเซอร์ดิน:", ["ความชื้น in ดิน (%)", "pH ของดิน", "ค่าปุ๋ยไนโตรเจน (N)"])
        df_soil = fetch_data("SELECT Timestamp, Value FROM Sensor_Logs WHERE Sensor_Type = ? ORDER BY Timestamp DESC LIMIT 15", (soil_sensor,))
        if not df_soil.empty:
            df_soil['Timestamp'] = pd.to_datetime(df_soil['Timestamp'])
            df_soil.set_index('Timestamp', inplace=True)
            st.line_chart(df_soil)
        else: st.info("ยังไม่มีข้อมูลบันทึกจากเซ็นเซอร์ดินประเภทนี้")

    with tab_water:
        water_sensor = st.selectbox("เลือกดูประวัติเซ็นเซอร์น้ำ:", ["pH ของน้ำ", "ออกซิเจนละลายน้ำ (DO)", "อุณหภูมิน้ำ (°C)"])
        df_water = fetch_data("SELECT Timestamp, Value FROM Sensor_Logs WHERE Sensor_Type = ? ORDER BY Timestamp DESC LIMIT 15", (water_sensor,))
        if not df_water.empty:
            df_water['Timestamp'] = pd.to_datetime(df_water['Timestamp'])
            df_water.set_index('Timestamp', inplace=True)
            st.line_chart(df_water)
        else: st.info("ยังไม่มีข้อมูลบันทึกจากเซ็นเซอร์น้ำประเภทนี้")

# --- โมดูลที่ 5: จัดการข้อมูล (Edit Data) ---
elif choice == "5. จัดการข้อมูล (Edit Data)":
    st.header("⚙️ ระบบหลังบ้าน - ลบข้อมูลที่กรอกผิดพลาด")
    tab_del_crop, tab_del_finance = st.tabs(["🌱 ลบรอบการปลูก", "💰 ลบบัญชีรายรับ-รายจ่าย"])
    with tab_del_crop:
        st.subheader("🗑️ ลบข้อมูลรอบการปลูก (Cascading Delete)")
        df_cycles = fetch_data("SELECT * FROM Planting_Cycles ORDER BY Plant_Date DESC")
        if not df_cycles.empty:
            st.dataframe(df_cycles, use_container_width=True)
            del_cycle_id = st.selectbox("เลือกรหัสรอบการปลูกที่ต้องการลบทิ้งถาวร:", ["-- เลือกใบงาน --"] + df_cycles['Cycle_ID'].tolist())
            if st.button("🚨 ยืนยันการลบข้อมูลถาวร") and del_cycle_id != "-- เลือกใบงาน --":
                run_query("DELETE FROM Planting_Cycles WHERE Cycle_ID = ?", (del_cycle_id,))
                run_query("DELETE FROM Tasks WHERE Cycle_ID = ?", (del_cycle_id,))
                run_query("DELETE FROM Expenses WHERE Cycle_ID = ?", (del_cycle_id,))
                run_query("DELETE FROM Revenues WHERE Cycle_ID = ?", (del_cycle_id,))
                st.success(f"🗑️ ลบข้อมูลรอบปลูก {del_cycle_id} เรียบร้อยแล้ว!"); st.rerun()
        else: st.info("ไม่มีข้อมูลรอบการปลูกให้ลบ")
        
    with tab_del_finance:
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(fetch_data("SELECT * FROM Expenses ORDER BY Exp_ID DESC"), use_container_width=True)
            del_exp = st.number_input("พิมพ์รหัส Exp_ID ที่ต้องการลบ", min_value=0, step=1)
            if st.button("🗑️ ลบรายการรายจ่าย") and del_exp > 0:
                run_query("DELETE FROM Expenses WHERE Exp_ID = ?", (del_exp,))
                st.success("ลบรายการสำเร็จ"); st.rerun()
        with col2:
            st.dataframe(fetch_data("SELECT * FROM Revenues ORDER BY Rev_ID DESC"), use_container_width=True)
            del_rev = st.number_input("พิมพ์รหัส Rev_ID ที่ต้องการลบ", min_value=0, step=1)
            if st.button("🗑️ ลบรายการรายรับ") and del_rev > 0:
                run_query("DELETE FROM Revenues WHERE Rev_ID = ?", (del_rev,))
                st.success("ลบรายการสำเร็จ"); st.rerun()
