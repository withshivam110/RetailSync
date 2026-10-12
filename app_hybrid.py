import pandas as pd
import psycopg2
from pymongo import MongoClient
import streamlit as st

# --- 1. MULTI-SERVER CONFIGURATION ---
# Define all your database environments here
SERVERS = {
    "srv_prod": {
        "name": "Production Server1",
        "badge": "LIVE",
        "desc": "Primary operational cluster for US orders & catalog",
        "pg": {
            "host": "localhost",
            "port": "5432",
            "database": "retailsync1",
            "user": "postgres",
            "password": "0816",
        },
        "mongo": {
            "uri": "mongodb://localhost:27017/",
            "database": "e_commerce_db",
        },
    },
    "srv_backup": {
        "name": "Backup Server2",
        "badge": "REPLICA",
        "desc": "Failover replica and read-only analytical database",
        "pg": {
            "host": "localhost",  # Replace with secondary/EU IP
            "port": "543",
            "database": "retailsync2",
            "user": "postgres",
            "password": "0816",
        },
        "mongo": {
            "uri": "mongodb://localhost:27017/",  # Replace with secondary MongoDB URI
            "database": "e_commerce_db",
        },
    },
    "srv_dev": {
        "name": "Server3",
        "badge": "REPLICA",
        "desc": "Development sandbox and QA testing database",
        "pg": {
            "host": "localhost",
            "port": "5432",
            "database": "retailsync3",
            "user": "postgres",
            "password": "0816",
        },
        "mongo": {
            "uri": "mongodb://localhost:27017/",
            "database": "e_commerce_db",
        },
    },
}

# --- 2. STREAMLIT UI CONFIGURATION ---
st.set_page_config(
    page_title="Multi-Server Hybrid Retail Sync Dashboard",
    layout="wide",
)

# Animated CSS: gradient background, staggered card entrance, glow, pulse,
# shimmer divider, animated title, tab and table transitions
st.markdown(
    """
    <style>
    /* ---------- Keyframes ---------- */
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(24px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes pulseGlow {
        0%   { box-shadow: 0 0 0 0 rgba(0, 188, 212, 0.55); }
        70%  { box-shadow: 0 0 0 14px rgba(0, 188, 212, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 188, 212, 0); }
    }
    @keyframes dotPulse {
        0%, 100% { transform: scale(1);   opacity: 1; }
        50%      { transform: scale(1.7); opacity: 0.45; }
    }
    @keyframes shimmer {
        0%   { background-position: -600px 0; }
        100% { background-position: 600px 0; }
    }
    @keyframes titleGradient {
        0%   { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    @keyframes floatY {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-4px); }
    }
    @keyframes borderFlow {
        0%   { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
    }

    /* ---------- Page background ---------- */
    .stApp {
        background: linear-gradient(-45deg, #0b0f17, #101826, #0d1b24, #14111f);
        background-size: 400% 400%;
        animation: gradientShift 22s ease infinite;
    }

    /* ---------- Animated title ---------- */
    h1 {
        background: linear-gradient(90deg, #00bcd4, #4caf50, #7c4dff, #00bcd4);
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: titleGradient 6s linear infinite, fadeInUp 0.8s ease both;
    }
    .stMarkdown p {
        animation: fadeIn 1.1s ease both;
    }

    /* ---------- Server cards ---------- */
    .server-card {
        position: relative;
        overflow: hidden;
        padding: 14px 18px;
        border-radius: 12px;
        border: 1px solid #333842;
        background-color: #1e222b;
        margin-bottom: 10px;
        transition: transform 0.25s ease, border-color 0.25s ease,
                    box-shadow 0.25s ease, background-color 0.25s ease;
        text-decoration: none !important;
        display: block;
        opacity: 0;
        animation: fadeInUp 0.7s ease forwards;
    }
    .server-card::before {
        content: "";
        position: absolute;
        top: 0; left: -120%;
        width: 60%; height: 100%;
        background: linear-gradient(
            120deg, transparent, rgba(255, 255, 255, 0.10), transparent);
        transition: left 0.6s ease;
    }
    .server-card:hover::before {
        left: 140%;
    }
    .server-card:hover {
        transform: translateY(-5px) scale(1.015);
        border-color: #4CAF50;
        box-shadow: 0 10px 26px rgba(76, 175, 80, 0.22);
    }
    .server-card-active {
        border: 2px solid #00bcd4 !important;
        background-color: #162a38 !important;
        animation: fadeInUp 0.7s ease forwards, pulseGlow 2.4s ease-out infinite 0.8s;
    }
    div[data-testid="column"]:nth-child(1) .server-card { animation-delay: 0.05s; }
    div[data-testid="column"]:nth-child(2) .server-card { animation-delay: 0.20s; }
    div[data-testid="column"]:nth-child(3) .server-card { animation-delay: 0.35s; }

    .server-title {
        font-weight: 700;
        font-size: 16px;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .server-desc {
        font-size: 12px;
        color: #a0aec0;
        margin-bottom: 8px;
    }
    .server-badge {
        display: inline-block;
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 4px;
        background: #2d3748;
        color: #e2e8f0;
        font-weight: 600;
        letter-spacing: 0.6px;
    }
    .server-badge::before {
        content: "";
        display: inline-block;
        width: 7px; height: 7px;
        margin-right: 7px;
        border-radius: 50%;
        background: #4caf50;
        animation: dotPulse 1.6s ease-in-out infinite;
    }
    .server-card-active .server-badge::before {
        background: #00bcd4;
    }

    /* ---------- Divider shimmer ---------- */
    hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(
            90deg, transparent 0%, #00bcd4 50%, transparent 100%) !important;
        background-size: 600px 100% !important;
        animation: shimmer 3.2s linear infinite;
        opacity: 0.8;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1420, #141b2a);
        border-right: 1px solid #222a3a;
        animation: slideInLeft 0.7s ease both;
    }
    section[data-testid="stSidebar"] a {
        display: inline-block;
        transition: transform 0.2s ease, color 0.2s ease;
    }
    section[data-testid="stSidebar"] a:hover {
        transform: translateX(6px);
        color: #00bcd4 !important;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        animation: fadeInUp 0.8s ease both;
    }
    section[data-testid="stSidebar"] .stMarkdown p {
        animation: slideInLeft 0.7s ease both;
    }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {
        transition: transform 0.2s ease, color 0.2s ease, background 0.2s ease;
        border-radius: 8px 8px 0 0;
    }
    button[data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        background: rgba(0, 188, 212, 0.10);
    }
    div[data-baseweb="tab-highlight"] {
        background: linear-gradient(90deg, #00bcd4, #4caf50, #7c4dff, #00bcd4) !important;
        background-size: 300% 100% !important;
        animation: borderFlow 4s linear infinite;
        height: 3px !important;
    }
    div[data-baseweb="tab-panel"] {
        animation: fadeInUp 0.55s ease both;
    }

    /* ---------- Tables, metrics, alerts, expanders ---------- */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        border: 1px solid #262d3d;
        transition: box-shadow 0.3s ease, border-color 0.3s ease;
        animation: fadeInUp 0.7s ease both;
    }
    div[data-testid="stDataFrame"]:hover {
        border-color: #00bcd4;
        box-shadow: 0 8px 24px rgba(0, 188, 212, 0.15);
    }
    div[data-testid="stMetric"] {
        padding: 14px 16px;
        border-radius: 12px;
        background: #1a2030;
        border: 1px solid #2a3246;
        transition: transform 0.25s ease, box-shadow 0.25s ease,
                    border-color 0.25s ease;
        animation: fadeInUp 0.7s ease both;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: #4caf50;
        box-shadow: 0 10px 22px rgba(76, 175, 80, 0.18);
    }
    div[data-testid="stMetricValue"] {
        animation: floatY 3.5s ease-in-out infinite;
    }
    div[data-testid="stAlert"] {
        animation: slideInLeft 0.6s ease both;
    }
    div[data-testid="stExpander"] {
        border-radius: 10px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        animation: fadeInUp 0.7s ease both;
    }
    div[data-testid="stExpander"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    }
    h2, h3 {
        animation: slideInLeft 0.6s ease both;
    }
    a {
        transition: color 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 3. URL QUERY PARAMETER HANDLING (LINK NAVIGATION) ---
# Read current server from URL link: ?server=srv_prod
active_server_id = st.query_params.get("server", "srv_prod")

if active_server_id not in SERVERS:
  active_server_id = "srv_prod"

active_server = SERVERS[active_server_id]

# --- 4. TOP LINK NAVIGATION BAR ---
st.title("Hybrid Multi-Server Retail Sync Dashboard")
st.markdown(
    "Click any of the server links below to inspect and fetch data from that"
    " specific server:"
)

# Render Clickable Links in Columns
cols = st.columns(len(SERVERS))
for col, (srv_id, srv_data) in zip(cols, SERVERS.items()):
  with col:
    is_active = srv_id == active_server_id
    card_class = (
        "server-card server-card-active" if is_active else "server-card"
    )
    active_marker = " (Connected)" if is_active else ""

    html_card = f"""
        <a href="?server={srv_id}" target="_self" class="{card_class}">
            <div class="server-title">{srv_data['name']}{active_marker}</div>
            <div class="server-desc">{srv_data['desc']}</div>
            <span class="server-badge">{srv_data['badge']}</span>
        </a>
        """
    st.markdown(html_card, unsafe_allow_html=True)

st.divider()

# --- 5. SIDEBAR LINKS & SERVER INFO ---
st.sidebar.header("Quick Server Links")
for srv_id, srv_data in SERVERS.items():
  icon = ">>" if srv_id == active_server_id else "-"
  st.sidebar.markdown(
      f"{icon} [{srv_data['name']}](?server={srv_id})",
      help=f"Connect to {srv_data['name']}",
  )

st.sidebar.divider()
st.sidebar.subheader("Active Server Specs")
st.sidebar.markdown(f"**PostgreSQL Host:** `{active_server['pg']['host']}`")
st.sidebar.markdown(f"**PostgreSQL Port:** `{active_server['pg']['port']}`")
st.sidebar.markdown(f"**PostgreSQL DB:** `{active_server['pg']['database']}`")
st.sidebar.markdown(f"**MongoDB DB:** `{active_server['mongo']['database']}`")


# --- 6. CONNECTION HANDLING (CACHED PER SERVER) ---
@st.cache_resource
def get_postgres_connection(host, database, user, password, port):
  return psycopg2.connect(
      host=host,
      database=database,
      user=user,
      password=password,
      port=port,
      connect_timeout=3,
  )


@st.cache_resource
def get_mongo_database(uri, db_name):
  client = MongoClient(uri, serverSelectionTimeoutMS=3000)
  client.admin.command("ping")  # Test connectivity
  return client[db_name]


# Connect to the selected server
pg_conn = None
mongo_db = None

try:
  pg_conn = get_postgres_connection(
      host=active_server["pg"]["host"],
      database=active_server["pg"]["database"],
      user=active_server["pg"]["user"],
      password=active_server["pg"]["password"],
      port=active_server["pg"]["port"],
  )
except Exception as e:
  st.error(
      f"Failed to connect to PostgreSQL on **{active_server['name']}**: {e}"
  )

try:
  mongo_db = get_mongo_database(
      uri=active_server["mongo"]["uri"],
      db_name=active_server["mongo"]["database"],
  )
except Exception as e:
  st.error(
      f"Failed to connect to MongoDB on **{active_server['name']}**: {e}"
  )


# --- 7. DATA FETCHING FUNCTIONS ---
def fetch_postgres_data(conn):
  if conn is None:
    return (
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )
  try:
    df_orders = pd.read_sql("SELECT * FROM orders ORDER BY order_id;", conn)
    df_inventory = pd.read_sql(
        "SELECT * FROM inventory ORDER BY product_id;", conn
    )
    df_billing = pd.read_sql("SELECT * FROM billing ORDER BY bill_id;", conn)

    join_query = """
            SELECT billing.bill_id, billing.order_id, billing.bill_status, 
                   orders.customer_id, orders.total_amount, orders.status AS order_status
            FROM billing
            JOIN orders ON billing.order_id = orders.order_id
            WHERE billing.bill_status = 'unpaid';
        """
    df_unpaid = pd.read_sql(join_query, conn)
    return df_orders, df_inventory, df_billing, df_unpaid
  except Exception as e:
    st.warning(f"PostgreSQL Query Error on this server: {e}")
    return (
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )


def fetch_mongo_data(db):
  if db is None:
    return pd.DataFrame(), pd.DataFrame()
  try:
    df_products = pd.DataFrame(list(db.products.find({}, {"_id": 0})))
    df_reviews = pd.DataFrame(list(db.reviews.find({}, {"_id": 0})))
    return df_products, df_reviews
  except Exception as e:
    st.warning(f"MongoDB Query Error on this server: {e}")
    return pd.DataFrame(), pd.DataFrame()


# Query current server data
df_orders, df_inventory, df_billing, df_unpaid = fetch_postgres_data(pg_conn)
df_products, df_reviews = fetch_mongo_data(mongo_db)


# --- 8. DASHBOARD TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "PostgreSQL: Orders & Billing",
    "PostgreSQL: Inventory & Unpaid Query",
    "MongoDB: Products & Reviews",
    "Unified Summary & Metrics",
    "Multi-Server Live Status",
])

with tab1:
  st.subheader(f"PostgreSQL - Orders & Billing ({active_server['name']})")
  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### Orders (`orders`)")
    if not df_orders.empty:
      st.dataframe(df_orders, use_container_width=True)
    else:
      st.info("No order records found on this server.")

  with col2:
    st.markdown("### Billing (`billing`)")
    if not df_billing.empty:
      st.dataframe(df_billing, use_container_width=True)
    else:
      st.info("No billing records found on this server.")

with tab2:
  st.subheader(f"PostgreSQL - Inventory & Joins ({active_server['name']})")
  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### Inventory Stock (`inventory`)")
    if not df_inventory.empty:
      st.dataframe(df_inventory, use_container_width=True)
    else:
      st.info("No inventory records found on this server.")

  with col2:
    st.markdown("### Unpaid Bills (SQL JOIN Query)")
    if not df_unpaid.empty:
      st.dataframe(df_unpaid, use_container_width=True)
    else:
      st.success("No unpaid bills found on this server!")

with tab3:
  st.subheader(f"MongoDB - Document Collections ({active_server['name']})")
  col1, col2 = st.columns(2)

  with col1:
    st.markdown("### Product Catalog (`products`)")
    if not df_products.empty:
      st.dataframe(df_products, use_container_width=True)
    else:
      st.info("No products found in MongoDB on this server.")

  with col2:
    st.markdown("### Customer Reviews (`reviews`)")
    if not df_reviews.empty:
      st.dataframe(df_reviews, use_container_width=True)
    else:
      st.info("No customer reviews found in MongoDB on this server.")

with tab4:
  st.subheader(f"Cross-Database Summary for {active_server['name']}")
  col1, col2, col3, col4 = st.columns(4)

  col1.metric("Postgres Orders", len(df_orders))
  col2.metric("Postgres Inventory Items", len(df_inventory))
  col3.metric("Mongo Products", len(df_products))
  col4.metric("Mongo Reviews", len(df_reviews))

  st.markdown("---")
  if not df_orders.empty and "total_amount" in df_orders.columns:
    total_rev = df_orders["total_amount"].astype(float).sum()
    st.metric("Total PostgreSQL Order Revenue", f"${total_rev:,.2f}")

with tab5:
  st.subheader("Live Health Check for All Configured Servers")
  st.markdown("Click any server link below to navigate to it directly:")

  for srv_id, srv in SERVERS.items():
    with st.expander(
        f"Server: {srv['name']} ({srv['badge']})",
        expanded=(srv_id == active_server_id),
    ):
      col_a, col_b, col_c = st.columns([2, 2, 1])

      # Test Postgres
      with col_a:
        try:
          test_p = psycopg2.connect(
              host=srv["pg"]["host"],
              database=srv["pg"]["database"],
              user=srv["pg"]["user"],
              password=srv["pg"]["password"],
              port=srv["pg"]["port"],
              connect_timeout=2,
          )
          test_p.close()
          st.success(
              f"PostgreSQL Online: `{srv['pg']['host']}:{srv['pg']['port']}`"
          )
        except Exception as e:
          st.error(f"PostgreSQL Offline: {e}")

      # Test Mongo
      with col_b:
        try:
          test_m = MongoClient(
              srv["mongo"]["uri"], serverSelectionTimeoutMS=2000
          )
          test_m.admin.command("ping")
          st.success(f"MongoDB Online: `{srv['mongo']['database']}`")
        except Exception as e:
          st.error(f"MongoDB Offline: {e}")

      with col_c:
        st.markdown(f"[Switch to this Server](?server={srv_id})")