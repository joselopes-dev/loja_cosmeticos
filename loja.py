import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread
import os

# ==================== CONFIGURAÇÕES ====================
TOKEN = "8660458553:AAHUWunQoRa8cysxS8DETtwJJ6VHfGTAtLI"                    # Token do @BotFather
ADMIN_ID = 8937649637                               # ID do atendente


bot = telebot.TeleBot(TOKEN)

# ==================== PRODUTOS ====================
PRODUTOS = {
    "skin": [
        {
            "id": "skin1",
            "nome": "Sabonete todo dia",
            "preco": 34.90,
            "descricao": "Sabonete em Barra Puro Vegetal Tododia Alecrim e Sálvia",
            "imagem": "./sabonete-tododia.png"
        },
        {
            "id": "skin2",
            "nome": "Sabonete Sortido",
            "preco": 40.90,
            "descricao": "Sabonete Sortido Puro Vegetal Erva Doce",
            "imagem": "./sabonete-2.png"
        },
    ],
    "make": [
        {
            "id": "make1",
            "nome": "Base Sérum",
            "preco": 179.90,
            "descricao": "Base Sérum Nude Me Una",
            "imagem": "./una-1.png"
        },
        {
            "id": "make2",
            "nome": "Batom Líquido Matte",
            "preco": 19.96,
            "descricao": "Batom Líquido Matte Longa Duração Faces",
            "imagem": "./deleniador-1.png"
        },
    ],
    "cabelo": [
        {
            "id": "cabelo1",
            "nome": "Shampoo + Condicionador",
            "preco": 69.90,
            "descricao": "Kit Lumina Shampoo e Condicionador Hidratação e Proteção Antipoluição (2 produtos)",
            "imagem": "./shampoo-1.png"
        },
    ]
}

# ==================== FUNÇÕES ====================
def enviar_produto(chat_id, produto):
    caption = (
        f"*{produto['nome']}*\n"
        f"💰 R$ {produto['preco']:.2f}\n\n"
        f"{produto['descricao']}\n\n"
        f"Digite *EU QUERO {produto['id']}* para comprar"
    )
    if os.path.exists(produto["imagem"]):
        with open(produto["imagem"], "rb") as foto:
            bot.send_photo(chat_id, foto, caption=caption, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, caption + "\n\n⚠️ (imagem não encontrada)", parse_mode="Markdown")

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💄 Catálogo", "💰 Promoções")
    markup.add("📦 Meu Pedido", "💬 Falar com atendente")
    bot.send_message(
        message.chat.id,
        f"Olá {message.from_user.first_name}! ✨\nBem-vinda à *Beleza Pura*\n\nO que você deseja fazer?",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text and "Catálogo" in m.text)
def catalogo(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧴 Skincare", callback_data="cat_skin"),
        types.InlineKeyboardButton("💄 Maquiagem", callback_data="cat_make"),
        types.InlineKeyboardButton("💇 Cabelo", callback_data="cat_cabelo"),
    )
    bot.send_message(message.chat.id, "Escolha uma categoria:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def mostrar_categoria(call):
    categoria = call.data.replace("cat_", "")
    produtos = PRODUTOS.get(categoria, [])
    if not produtos:
        bot.answer_callback_query(call.id, "Nenhum produto nessa categoria ainda.")
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"📦 Produtos de *{categoria.capitalize()}*:", parse_mode="Markdown")
    for produto in produtos:
        enviar_produto(call.message.chat.id, produto)

@bot.message_handler(func=lambda m: m.text and "eu quero" in m.text.lower())
def iniciar_compra(message):
    texto = message.text.lower()
    produto_id = None
    produto_nome = ""
    produto_preco = 0
    for cat in PRODUTOS.values():
        for p in cat:
            if p["id"] in texto:
                produto_id = p["id"]
                produto_nome = p["nome"]
                produto_preco = p["preco"]
                break
        if produto_id:
            break
    if not produto_id:
        bot.send_message(message.chat.id, "Não entendi qual produto. Digite por exemplo:\n*EU QUERO skin1*", parse_mode="Markdown")
        return
    bot.send_message(
        message.chat.id,
        f"Perfeito! Você escolheu: *{produto_nome}* (R$ {produto_preco:.2f})\n\n"
        f"Agora me envie:\n1. Seu nome completo\n2. CEP\n3. Forma de pagamento (PIX ou Cartão)\n\n"
        f"Pode mandar tudo em uma única mensagem 😊",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and any(x in m.text.lower() for x in ["cep", "pix", "cartão", "cartao", "pagamento"]))
def receber_dados_compra(message):
    user = message.from_user
    texto_pedido = (
        f"🛍️ *NOVO PEDIDO RECEBIDO*\n\n"
        f"👤 Cliente: {user.first_name} {user.last_name or ''}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Username: @{user.username or 'não tem'}\n\n"
        f"📝 Dados enviados:\n{message.text}\n\n"
        f"👉 Entre em contato com o cliente."
    )
    try:
        bot.send_message(ADMIN_ID, texto_pedido, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Pedido enviado para a equipe! Em breve um atendente te chama 💖")
    except:
        bot.send_message(message.chat.id, "Erro ao enviar para o atendente. Tente novamente.")

@bot.message_handler(func=lambda m: m.text and "Falar com atendente" in m.text)
def falar_atendente(message):
    user = message.from_user
    aviso = (
        f"💬 *Cliente quer falar com atendente*\n\n"
        f"👤 {user.first_name} {user.last_name or ''}\n"
        f"🆔 `{user.id}`\n"
        f"🔗 @{user.username or 'não tem'}"
    )
    try:
        bot.send_message(ADMIN_ID, aviso, parse_mode="Markdown")
        bot.send_message(message.chat.id, "Já avisei um atendente! Em breve ele te responde 💕")
    except:
        bot.send_message(message.chat.id, "Não consegui avisar o atendente agora.")

app = Flask('')
@app.route('/')
def home():
    return "Bot online"

# ==========================================================
# INICIAR O BOT
# ==========================================================

if __name__ == "__main__":
    print("Bot da loja iniciado...")
    print("Pressione Ctrl + C para parar.")
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.remove_webhook()
    time.sleep(3)
    bot.infinity_polling()
