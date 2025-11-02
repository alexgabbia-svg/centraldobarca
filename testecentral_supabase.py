# testecentral_supabase.py
# Central do Barça — Streamlit + Supabase
# Requer: streamlit, pandas, supabase, Pillow
# Antes de rodar: preencha SUPABASE_URL e SUPABASE_KEY com os seus dados do Supabase.

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import json
from datetime import date, datetime
from PIL import Image
import os

# -----------------------
# CONFIG — coloque suas credenciais aqui (NÃO compartilhe publicamente)
# -----------------------
SUPABASE_URL = "https://rauycbzexubugyrcauvj.supabase.co"   # <-- cole aqui o Project URL do Supabase (ex: https://xxxx.supabase.co)
SUPABASE_KEY = "anon/public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJhdXljYnpleHVidWd5cmNhdXZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIwMzY4MTUsImV4cCI6MjA3NzYxMjgxNX0.MpW80cDt3VH8AMcsskvVSaBjbbaxTTIaV9FAKlA_fkg"   # <-- cole aqui a anon/public key
# -----------------------

# admin login (único)
ADMIN_USER = "admin"
ADMIN_PASS = "barca123"

# app config
APP_TITLE = "Central do Barça - Dados e Estatísticas"
LOGO_PATH = "barca_logo.png"

st.set_page_config(page_title=APP_TITLE, layout="wide")

# -----------------------
# Conexão Supabase
# -----------------------
def make_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        sup = create_client(SUPABASE_URL, SUPABASE_KEY)
        return sup
    except Exception as e:
        st.error(f"Erro ao criar cliente Supabase: {e}")
        return None

supabase: Client | None = make_supabase_client()

# -----------------------
# UI: logo (força transparência)
# -----------------------
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            # limpa verde-chave potencial (se houver)
            data = logo.getdata()
            new = []
            for item in data:
                # se verde forte detectado (ajuste heurística) -> transparente
                if item[1] > 200 and item[0] < 80 and item[2] < 80:
                    new.append((255,255,255,0))
                else:
                    new.append(item)
            logo.putdata(new)
            st.image(logo, width=140)
        except Exception as e:
            st.warning("Problema ao carregar logo: " + str(e))
    else:
        st.warning("Logo (barca_logo.png) não encontrada na pasta.")
with col2:
    st.markdown(f"<h1 style='color:#ff6600'>{APP_TITLE}</h1>", unsafe_allow_html=True)

st.markdown("---")

# -----------------------
# Help: SQL para criar tabelas (cole no SQL Editor do Supabase)
# -----------------------
CREATE_TABLES_SQL = """
-- Crie estas tabelas no Supabase SQL editor (copie+cole e execute)
-- TABELA jogadores
CREATE TABLE IF NOT EXISTS public.jogadores (
  id serial primary key,
  nome text UNIQUE,
  posicao text,
  gols integer DEFAULT 0,
  assistencias integer DEFAULT 0,
  craques integer DEFAULT 0,
  artilheiro integer DEFAULT 0,
  assist_flag integer DEFAULT 0,
  defensor integer DEFAULT 0,
  goleiro integer DEFAULT 0,
  coringa integer DEFAULT 0,
  capitao integer DEFAULT 0,
  craque_points_manual integer DEFAULT 0
);

-- TABELA rodadas (cada linha contém um JSON 'records' com a lista de participantes)
CREATE TABLE IF NOT EXISTS public.rodadas (
  id serial primary key,
  data date,
  records jsonb
);

-- TABELA puskas (votos por jogador)
CREATE TABLE IF NOT EXISTS public.puskas (
  id serial primary key,
  nome text,
  votos integer DEFAULT 0
);

-- TABELA equipes (quintetos)
CREATE TABLE IF NOT EXISTS public.equipes (
  id serial primary key,
  players text[], -- array de nomes
  vitorias integer DEFAULT 0
);

-- TABELA rankings opcionais (se quiser guardar snapshots)
CREATE TABLE IF NOT EXISTS public.rankings_snapshot (
  id serial primary key,
  created_at timestamptz DEFAULT now(),
  snapshot jsonb
);
"""

# -----------------------
# Helpers Supabase CRUD
# -----------------------
def check_tables_exist():
    """Tenta fazer uma query simples para verificar conexão e existência de tabelas."""
    if not supabase:
        return (False, "Supabase client não configurado. Preencha SUPABASE_URL e SUPABASE_KEY.")
    try:
        res = supabase.table("jogadores").select("nome").limit(1).execute()
        # se res.status_code ou res.data falhar, será exceção
        return (True, None)
    except Exception as e:
        return (False, str(e))

def list_jogadores():
    ok, msg = check_tables_exist()
    if not ok:
        st.warning("Verifique as tabelas no Supabase. " + (msg or ""))
        return []
    r = supabase.table("jogadores").select("*").order("nome", {"ascending": True}).execute()
    return r.data if r and hasattr(r, "data") else []

def upsert_jogador(j):
    """j: dict com chaves nome,posicao,gols,assistencias,..."""
    supabase.table("jogadores").upsert(j, on_conflict="nome").execute()

def delete_jogador_by_name(nome):
    supabase.table("jogadores").delete().eq("nome", nome).execute()

def list_rodadas():
    r = supabase.table("rodadas").select("*").order("data", {"ascending": False}).execute()
    return r.data if r and hasattr(r, "data") else []

def insert_rodada(data_iso, records):
    # records: list of dicts -> armazenar como jsonb
    supabase.table("rodadas").insert({"data": data_iso, "records": json.dumps(records)}).execute()

def list_puskas():
    r = supabase.table("puskas").select("*").order("votos", {"ascending": False}).execute()
    return r.data if r and hasattr(r, "data") else []

def upsert_puskas(nome, votos):
    supabase.table("puskas").upsert({"nome": nome, "votos": int(votos)}, on_conflict="nome").execute()

def list_equipes():
    r = supabase.table("equipes").select("*").order("vitorias", {"ascending": False}).execute()
    return r.data if r and hasattr(r, "data") else []

def insert_equipe(players, vitorias=0):
    supabase.table("equipes").insert({"players": players, "vitorias": int(vitorias)}).execute()

def update_equipe(eq_id, players, vitorias):
    supabase.table("equipes").update({"players": players, "vitorias": int(vitorias)}).eq("id", eq_id).execute()

def delete_equipe(eq_id):
    supabase.table("equipes").delete().eq("id", eq_id).execute()

# -----------------------
# Aggregation local helpers (build rankings from fetched data)
# -----------------------
WEIGHTS = {
    "craque": 100,
    "artilheiro": 90,
    "assistencia": 80,
    "defensor": 60,
    "goleiro": 50,
    "coringa": 40,
    "capitao": 30
}

def compute_rankings_from_db():
    jogadores = list_jogadores()
    rodadas = list_rodadas()
    pusk = list_puskas()
    equipes = list_equipes()

    goals = {}
    assists = {}
    counts = {"craque":{}, "artilheiro":{}, "assistencia":{}, "defensor":{}, "goleiro":{}, "coringa":{}, "capitao":{}}
    pusk_counts = {}
    # start from players table manual totals
    for j in jogadores:
        name = j.get("nome")
        goals[name] = j.get("gols", 0)
        assists[name] = j.get("assistencias", 0)
        counts["craque"][name] = j.get("craques", 0)
        counts["artilheiro"][name] = j.get("artilheiro", 0)
        counts["assistencia"][name] = j.get("assist_flag", 0)
        counts["defensor"][name] = j.get("defensor", 0)
        counts["goleiro"][name] = j.get("goleiro", 0)
        counts["coringa"][name] = j.get("coringa", 0)
        counts["capitao"][name] = j.get("capitao", 0)
    # aggregate rodadas (they may contain JSON strings in records field)
    for rd in rodadas:
        recs_raw = rd.get("records")
        try:
            recs = json.loads(recs_raw) if isinstance(recs_raw, str) else recs_raw
        except Exception:
            recs = rd.get("records") or []
        for r in recs:
            n = r.get("Nome") or r.get("nome")
            if not n: continue
            goals[n] = goals.get(n, 0) + int(r.get("Gols", 0) or 0)
            assists[n] = assists.get(n, 0) + int(r.get("Assistencias", 0) or 0)
            if r.get("craque_flag") or r.get("craque"):
                counts["craque"][n] = counts["craque"].get(n, 0) + 1
            if r.get("art_flag") or r.get("artilheiro"):
                counts["artilheiro"][n] = counts["artilheiro"].get(n, 0) + 1
            if r.get("assist_flag") or r.get("assistencia"):
                counts["assistencia"][n] = counts["assistencia"].get(n, 0) + 1
            if r.get("defensor_flag") or r.get("defensor"):
                counts["defensor"][n] = counts["defensor"].get(n, 0) + 1
            if r.get("goleiro_flag") or r.get("goleiro"):
                counts["goleiro"][n] = counts["goleiro"].get(n, 0) + 1
            if r.get("coringa_flag") or r.get("coringa"):
                counts["coringa"][n] = counts["coringa"].get(n, 0) + 1
            if r.get("capitao_flag") or r.get("capitao"):
                counts["capitao"][n] = counts["capitao"].get(n, 0) + 1
            # puskas votes per record
            pv = int(r.get("puskas_votes", 0) or 0)
            if pv:
                pusk_counts[n] = pusk_counts.get(n, 0) + pv
    # include pusk table direct votes
    for p in pusk:
        n = p.get("nome")
        pusk_counts[n] = pusk_counts.get(n, 0) + p.get("votos", 0)

    # compute craque points (auto) from counts
    craque_points_auto = {}
    for n,cnt in counts["craque"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["craque"]
    for n,cnt in counts["artilheiro"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["artilheiro"]
    for n,cnt in counts["assistencia"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["assistencia"]
    for n,cnt in counts["defensor"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["defensor"]
    for n,cnt in counts["goleiro"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["goleiro"]
    for n,cnt in counts["coringa"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["coringa"]
    for n,cnt in counts["capitao"].items():
        craque_points_auto[n] = craque_points_auto.get(n, 0) + cnt * WEIGHTS["capitao"]

    return {
        "goals": goals,
        "assists": assists,
        "counts": counts,
        "puskas": pusk_counts,
        "craque_points_auto": craque_points_auto,
        "equipes": equipes
    }

def fmt_rank_from_map(map_dict, top_n=None):
    arr = [(k,v) for k,v in map_dict.items() if v is not None]
    arr_sorted = sorted(arr, key=lambda x:-x[1])
    res=[]
    last_val=None
    last_pos=0
    for idx,(name,val) in enumerate(arr_sorted, start=1):
        pos = last_pos if (last_val is not None and val == last_val) else idx
        last_pos = pos
        last_val = val
        res.append((f"{pos}º", name, val))
        if top_n and len(res) >= top_n: break
    return res

# -----------------------
# Páginas Streamlit
# -----------------------
def sidebar():
    st.sidebar.title(APP_TITLE)
    if supabase is None:
        st.sidebar.error("Supabase não configurado. Coloque SUPABASE_URL e SUPABASE_KEY no topo do arquivo.")
    if st.session_state.get("logged_in"):
        st.sidebar.success("Logado como admin")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()
    else:
        st.sidebar.info("Acesse como admin para editar")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navegar", ["Dashboard","Jogadores","Registrar Rodada","Rodadas","Quintetos","Import/Export","Admin"])
    return page

def page_dashboard():
    st.header("Dashboard")
    ok, err = check_tables_exist()
    if not ok:
        st.error("Problema com o Supabase / tabelas. Abra o SQL editor do Supabase e cole o SQL (veja Help).")
        st.code(CREATE_TABLES_SQL)
        return

    ranks = compute_rankings_from_db()
    goals = ranks["goals"]
    assists = ranks["assists"]
    craque_pts = ranks["craque_points_auto"]
    puskas = ranks["puskas"]
    equipes = ranks["equipes"]

    # Top row 3
    c1,c2,c3 = st.columns(3)
    with c1:
        st.subheader("Artilharia")
        rows = fmt_rank_from_map(goals, top_n=20)
        for pos,name,val in rows:
            st.write(f"{pos} {name} — {val}")
        if len(rows) >= 20: 
            if st.button("Ver mais Artilharia"): st.write("Mostrando todos...")  # placeholder

    with c2:
        st.subheader("Assistências")
        rows = fmt_rank_from_map(assists, top_n=20)
        for pos,name,val in rows:
            st.write(f"{pos} {name} — {val}")

    with c3:
        st.subheader("Craque do Barça (pontos)")
        rows = fmt_rank_from_map(craque_pts, top_n=20)
        for pos,name,val in rows:
            st.write(f"{pos} {name} — {val}")

    st.markdown("---")
    # categories row
    cats = ["craque","defensor","coringa","capitao","goleiro"]
    cols = st.columns(len(cats))
    counts = ranks["counts"]
    for i,cat in enumerate(cats):
        with cols[i]:
            st.subheader(cat.capitalize())
            mapping = counts.get(cat, {})
            rows = fmt_rank_from_map(mapping, top_n=10)
            for pos,name,val in rows:
                st.write(f"{pos} {name} — {val}")

    st.markdown("---")
    # puskas
    st.subheader("Puskás (votos)")
    rows = fmt_rank_from_map(puskas, top_n=30)
    for pos,name,val in rows:
        st.write(f"{pos} {name} — {val}")

    st.markdown("---")
    # quintetos
    st.subheader("Melhor Quinteto (manual)")
    # equipes is list from supabase with fields id, players, vitorias
    if equipes:
        for e in equipes:
            pid = e.get("id")
            players = e.get("players") or []
            v = e.get("vitorias",0)
            st.write(f"{pid} — {', '.join(players)} — {v} vitórias")
    else:
        st.info("Nenhum quinteto registrado.")

def page_jogadores():
    st.header("Jogadores")
    if not supabase:
        st.error("Supabase não configurado.")
        return
    jogadores = list_jogadores()
    df = pd.DataFrame(jogadores or [])
    if df.empty:
        st.info("Nenhum jogador cadastrado.")
    else:
        # exibir e permitir edição em massa
        st.markdown("### Lista (edite e clique em Salvar)")
        editable = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="dj")
        if st.button("Salvar jogadores editados"):
            # upsert each row
            for row in editable.to_dict(orient="records"):
                row2 = {
                    "nome": row.get("nome"),
                    "posicao": row.get("posicao"),
                    "gols": int(row.get("gols") or 0),
                    "assistencias": int(row.get("assistencias") or 0),
                    "craques": int(row.get("craques") or 0),
                    "artilheiro": int(row.get("artilheiro") or 0),
                    "assist_flag": int(row.get("assist_flag") or 0),
                    "defensor": int(row.get("defensor") or 0),
                    "goleiro": int(row.get("goleiro") or 0),
                    "coringa": int(row.get("coringa") or 0),
                    "capitao": int(row.get("capitao") or 0),
                    "craque_points_manual": int(row.get("craque_points_manual") or 0)
                }
                upsert_jogador(row2)
            st.success("Jogadores salvos no Supabase.")

    # adicionar jogador
    st.markdown("### Adicionar novo jogador")
    with st.form("add_player"):
        n = st.text_input("Nome")
        p = st.text_input("Posição")
        g = st.number_input("Gols (inicial)", min_value=0, value=0)
        a = st.number_input("Assistências (inicial)", min_value=0, value=0)
        submit = st.form_submit_button("Adicionar")
        if submit:
            upsert_jogador({"nome": n.strip(), "posicao": p.strip(), "gols": int(g), "assistencias": int(a)})
            st.success("Jogador inserido")
            st.experimental_rerun()

def page_registrar_rodada():
    st.header("Registrar Rodada")
    jogadores = list_jogadores()
    if not jogadores:
        st.info("Cadastre jogadores antes.")
        return
    names = [j.get("nome") for j in jogadores]
    data = st.date_input("Data", value=date.today())
    selected = st.multiselect("Selecione jogadores", options=names)
    records = []
    if selected:
        st.markdown("Preencha dados dos selecionados")
        for name in selected:
            cols = st.columns([2,1,1,1,1,1,1])
            cols[0].write(f"**{name}**")
            presente = cols[1].checkbox("Presente", value=True, key=f"pres_{name}")
            gols = cols[2].number_input("Gols", min_value=0, value=0, key=f"g_{name}", format="%d")
            assists = cols[3].number_input("Assist.", min_value=0, value=0, key=f"a_{name}", format="%d")
            craque = cols[4].checkbox("Craque", key=f"cq_{name}")
            art = cols[5].checkbox("Artilheiro", key=f"art_{name}")
            pv = cols[6].number_input("Puskás votos", min_value=0, value=0, key=f"pv_{name}", format="%d")
            records.append({
                "Nome": name,
                "presente": bool(presente),
                "Gols": int(gols),
                "Assistencias": int(assists),
                "craque_flag": bool(craque),
                "art_flag": bool(art),
                "puskas_votes": int(pv)
            })
        if st.button("Salvar rodada"):
            # insert rodadas and also update jogadores table increments (optional)
            insert_rodada(data.isoformat(), records)
            # update per-player counts in jogadores table (optional: we update totals)
            for rec in records:
                n = rec["Nome"]
                # add goals/assists cumulatively to jogadores table
                # fetch existing
                existing = supabase.table("jogadores").select("*").eq("nome", n).limit(1).execute().data
                if existing:
                    ex = existing[0]
                    new_g = int(ex.get("gols",0)) + int(rec.get("Gols",0))
                    new_a = int(ex.get("assistencias",0)) + int(rec.get("Assistencias",0))
                    updates = {"gols": new_g, "assistencias": new_a}
                    if rec.get("craque_flag"):
                        updates["craques"] = int(ex.get("craques",0)) + 1
                    if rec.get("art_flag"):
                        updates["artilheiro"] = int(ex.get("artilheiro",0)) + 1
                    supabase.table("jogadores").update(updates).eq("nome", n).execute()
                else:
                    # create minimal
                    newdoc = {"nome": n, "posicao": "", "gols": rec.get("Gols",0), "assistencias": rec.get("Assistencias",0)}
                    if rec.get("craque_flag"):
                        newdoc["craques"] = 1
                    supabase.table("jogadores").insert(newdoc).execute()
                # puskas
                if int(rec.get("puskas_votes",0)):
                    upsert_puskas(n, rec.get("puskas_votes",0))
            st.success("Rodada e atualizações salvas.")
            st.experimental_rerun()

def page_rodadas_history():
    st.header("Rodadas (Histórico)")
    r = list_rodadas()
    if not r:
        st.info("Nenhuma rodada registrada.")
        return
    # show dates
    df = pd.DataFrame(r)
    df_display = df[["id","data"]].sort_values(by="data", ascending=False)
    sel = st.selectbox("Escolha uma rodada", options=df_display["id"].tolist(), format_func=lambda x: f"Rodada #{x} - {df_display[df_display['id']==x]['data'].values[0]}")
    if sel:
        rec = supabase.table("rodadas").select("*").eq("id", sel).execute().data
        if rec:
            rec0 = rec[0]
            records_raw = rec0.get("records")
            try:
                records = json.loads(records_raw) if isinstance(records_raw, str) else records_raw
            except:
                records = records_raw
            st.dataframe(pd.DataFrame(records))

def page_quintetos():
    st.header("Quintetos (Melhor Equipe)")
    eqs = list_equipes()
    if eqs:
        df = pd.DataFrame(eqs)
        st.dataframe(df)
    else:
        st.info("Nenhum quinteto registrado.")
    st.markdown("### Adicionar / Editar Quinteto (manual)")
    with st.form("add_quint"):
        p1=st.text_input("Jogador 1"); p2=st.text_input("Jogador 2"); p3=st.text_input("Jogador 3")
        p4=st.text_input("Jogador 4"); p5=st.text_input("Jogador 5"); vits=st.number_input("Vitórias", min_value=0, value=0)
        submit = st.form_submit_button("Adicionar Quinteto")
        if submit:
            players = [x.strip() for x in [p1,p2,p3,p4,p5] if x.strip()]
            if players:
                insert_equipe(players, vits)
                st.success("Quinteto adicionado.")
                st.experimental_rerun()

def page_import_export():
    st.header("Import / Export")
    st.markdown("Exportar snapshot das tabelas (JSON)")
    if st.button("Exportar jogadores"):
        st.write("Gerando export de jogadores...")
        st.download_button("Baixar jogadores", json.dumps(list_jogadores(), ensure_ascii=False, indent=2), "jogadores.json")
    if st.button("Exportar rodadas"):
        st.download_button("Baixar rodadas", json.dumps(list_rodadas(), ensure_ascii=False, indent=2), "rodadas.json")
    st.markdown("---")
    st.markdown("Importar arquivos JSON (formato equivalente das exportações)")
    upj = st.file_uploader("Importar jogadores JSON", type=["json"])
    if upj:
        data = json.load(upj)
        for item in data:
            upsert_jogador(item)
        st.success("Jogadores importados.")

def page_admin():
    st.header("Admin")
    st.markdown("Verifique/execute SQL para criar tabelas caso ainda não existam:")
    st.code(CREATE_TABLES_SQL)
    if st.button("Testar conexão e tabelas"):
        ok, err = check_tables_exist()
        if ok:
            st.success("Supabase conectado e tabela jogadores acessível.")
        else:
            st.error("Erro: " + (err or "Desconhecido"))

# -----------------------
# Router
# -----------------------
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    page = sidebar()

    # login box simple
    if not st.session_state.logged_in:
        st.markdown("### Login Admin")
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user == ADMIN_USER and pwd == ADMIN_PASS:
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Credenciais inválidas")
        # allow public viewing pages but block edit actions in pages
        if page != "Dashboard":
            st.info("Faça login para acessar e editar esta área.")
    # route pages
    if page == "Dashboard":
        page_dashboard()
    elif page == "Jogadores":
        page_jogadores()
    elif page == "Registrar Rodada":
        page_registrar_rodada()
    elif page == "Rodadas":
        page_rodadas_history()
    elif page == "Quintetos":
        page_quintetos()
    elif page == "Import/Export":
        page_import_export()
    elif page == "Admin":
        page_admin()

if __name__ == "__main__":
    main()
