import os
from supabase import create_client, Client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("URL:", url)
print("KEY (início):", key[:10] if key else "N/A")

if not url or not key:
    print("❌ ERRO: Variáveis não encontradas.")
else:
    try:
        supabase: Client = create_client(url, key)
        data = supabase.table("jogadores").select("*").limit(1).execute()
        print("✅ Conectado com sucesso! Tabelas acessíveis.")
        print(data)
    except Exception as e:
        print("❌ Erro ao conectar:", e)
