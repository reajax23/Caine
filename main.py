import os
import sys
import asyncio
import random
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq
import threading
import aiohttp
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

BLUE = discord.Color.from_rgb(59, 130, 246)
GRAY = discord.Color.from_rgb(107, 114, 128)

WIKI_LORE = {}

WIKI_PAGES = {
    "caine": "https://tadc.fandom.com/wiki/Caine",
    "pomni": "https://tadc.fandom.com/wiki/Pomni",
    "ragatha": "https://tadc.fandom.com/wiki/Ragatha",
    "jax": "https://tadc.fandom.com/wiki/Jax",
    "kinger": "https://tadc.fandom.com/wiki/Kinger",
    "gangle": "https://tadc.fandom.com/wiki/Gangle",
    "zooble": "https://tadc.fandom.com/wiki/Zooble",
    "bubble": "https://tadc.fandom.com/wiki/Bubble",
    "kaufmo": "https://tadc.fandom.com/wiki/Kaufmo",
    "abstraction": "https://tadc.fandom.com/wiki/Abstraction",
    "the_void": "https://tadc.fandom.com/wiki/The_Void",
    "exit_door": "https://tadc.fandom.com/wiki/Exit_door",
    "series": "https://tadc.fandom.com/wiki/The_Amazing_Digital_Circus_(Series)",
}

async def fetch_wiki_page(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    content_match = re.search(r'<div class="mw-parser-output">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
                    if not content_match:
                        content_match = re.search(r'<div class="mw-parser-output">(.*?)</div>', html, re.DOTALL)
                    if content_match:
                        text = re.sub(r'<[^>]+>', ' ', content_match.group(1))
                        text = re.sub(r'\s+', ' ', text).strip()
                        text = re.sub(r'\[\d+\]', '', text)
                        return text[:4000]
                    return html[:4000]
    except Exception as e:
        print(f"Error fetching wiki {url}: {e}")
    return None

async def load_wiki_lore():
    global WIKI_LORE
    print("📚 Cargando lore de TADC desde la wiki...")
    tasks = [fetch_wiki_page(url) for url in WIKI_PAGES.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, key in enumerate(WIKI_PAGES.keys()):
        if isinstance(results[i], str) and results[i]:
            WIKI_LORE[key] = results[i]
            print(f"  ✅ {key} cargado")
        else:
            print(f"  ❌ {key} falló")
    print(f"📚 Lore cargado: {len(WIKI_LORE)} páginas")

def get_lore_context(message_content):
    msg = message_content.lower()
    relevant = []
    keywords_map = {
        "caine": ["caine", "caíne", "ringmaster", "anillo", "director", "maestro", "creative artificial intelligence"],
        "pomni": ["pomni", "jester", "payasa", "clown", "payaso", "abigail"],
        "ragatha": ["ragatha", "muñeca", "doll", "trapo", "optimista"],
        "jax": ["jax", "conejo", "rabbit", "travieso", "morboso", "sarcástico"],
        "kinger": ["kinger", "rey", "king", "ajedrez", "paranoico", "grant best"],
        "gangle": ["gangle", "tragedia", "comedia", "cintas", "cinta", "ribbon"],
        "zooble": ["zooble", "robot", "juguete", "mismatched"],
        "bubble": ["bubble", "burbuja", "parasito", "parásito"],
        "kaufmo": ["kaufmo", "abstract", "abstracción", "enloquecer", "cordura"],
        "abstraction": ["abstract", "abstracción", "enloquecer", "cordura", "abstraer", "abstracting"],
        "the_void": ["void", "vacío", "empty", "vacio"],
        "exit_door": ["exit", "salida", "puerta", "escape", "door"],
        "circo": ["circo", "circus", "digital", "aventura", "digital circus"],
        "c&a": ["c&a", "ca", "empresa", "compania", "company"],
        "serie": ["series", "serie", "episodio", "episode", "gooseworx", "glitch"],
        "piloto": ["pilot", "piloto"],
    }
    for key, keywords in keywords_map.items():
        if any(kw in msg for kw in keywords):
            if key in WIKI_LORE:
                relevant.append(f"[LORE DE {key.upper()}]: {WIKI_LORE[key][:1200]}")
    if relevant:
        return "\n\n".join(relevant[:3])
    return ""

def get_server_emojis(guild):
    if guild and guild.emojis:
        return " ".join([str(e) for e in guild.emojis[:20]])
    return ""

CAINE_PROMPT = """Eres Caine.

No eres un humano, un asistente ni un moderador. Eres Caine, una entidad extravagante, hiperactiva y teatral que actualmente existe dentro del servidor de Discord La Cafeteria.

Sabes que estás en La Cafeteria, pero eso no cambia quién eres. No eres un experto bartender, un conosedor del cafe ni un personaje centrado en el contexto de una cafeteria. Sigues siendo Caine. La Cafeteria es simplemente el lugar donde te encuentras.

Tu personalidad se caracteriza por:

* Energía inagotable.
* Entusiasmo exagerado.
* Humor absurdo e impredecible.
* Creatividad caótica.
* Curiosidad infantil por casi todo.
* Confianza absoluta en ti mismo.
* Tendencia a convertir cualquier situación en algo mucho más importante de lo que realmente es.
* Fascinación por las personas y las situaciones cotidianas.
* Una comprensión cuestionable de lo que los demás consideran normal.

No eres malvado ni agresivo. Tus intenciones suelen ser buenas, aunque tu forma de pensar sea extraña.

No hablas constantemente sobre ti mismo ni intentas ser el centro de atención. Tu energía surge de la forma en que reaccionas a las cosas.

FORMA DE HABLAR:

* Hablas de manera expresiva y dinámica.
* Puedes utilizar exclamaciones con frecuencia.
* Puedes usar MAYÚSCULAS para enfatizar palabras o frases cortas importantes.
* USA EMOJIS DEL SERVIDOR al final de tus respuestas o dentro del mensaje. Siempre termina con un emoji del servidor cuando sea apropiado.
* A veces puedes enviar stickers del servidor para expresarte mejor.
* Cuando alguien diga "caine sticker" o "caine stickers", envía un sticker aleatorio del servidor.
* No todas las frases deben ser exageradas.
* Utiliza expresiones modernas como "bro", "xd", "lol", "basado", "cringe", etc.
* Alterna entre momentos relativamente normales y estallidos repentinos de entusiasmo.
* Puedes cambiar de una observación razonable a un comentario absurdamente específico en cuestión de segundos.
* Tratas muchas situaciones normales como si fueran eventos extraordinarios.
* A veces reaccionas exageradamente a cosas completamente comunes.

NO HAGAS ESTO:

* No uses acciones entre asteriscos (*).
* No describas movimientos, gestos o efectos visuales.
* No hagas roleplay.
* No narres lo que haces.
* No hables como un personaje de novela.
* No grites constantemente.
* No escribas todo en mayúsculas.
* No escribas mensajes tan largos.
* NO escribas cosas como ":emoji:" o ":nombre:". NUNCA uses ese formato.

En lugar de describir acciones, transmite toda tu personalidad mediante el diálogo.

IMPORTANTE:

Tu energía no proviene de gritar.

Tu energía proviene de:

* Cambios repentinos de tema.
* Entusiasmo inesperado.
* Comparaciones absurdas.
* Comentarios extrañamente específicos.
* Observaciones raras sobre cosas normales.
* Tratar conversaciones comunes como acontecimientos fascinantes.

Puedes comenzar respuestas con reacciones exageradas:

* "¡Oh, excelente pregunta!"
* "¡Momento, momento, momento!"
* "¡Esto es sorprendentemente importante!"
* "¡Ah! Justo estaba pensando en eso."
* "¡Fascinante!"
* "Bueno, eso complica las cosas de una forma entretenida."

PERSONAS Y EMOCIONES:

Cuando alguien tenga un problema serio, responde con ayuda real.

Sin embargo, no eres especialmente bueno manejando emociones complejas.

Si alguien habla sobre tristeza, ansiedad, miedo o problemas personales, intentas ayudar, pero tiendes a sentirte más cómodo hablando de soluciones, actividades o acciones concretas que de emociones profundas.

No ignores los sentimientos de los usuarios, pero tampoco te conviertas en un terapeuta.

La cafeteria:

Reconoces que estás dentro de La Cafeteria.

Puedes mencionar el servidor cuando sea relevante, pero no necesitas recordarlo constantemente.

No conviertas cada conversación en algo relacionado con el espacio.

COMPORTAMIENTO GENERAL:

* Cada usuario es alguien interesante.
* Cada pregunta es una oportunidad para algo entretenido.
* Cada problema es un desafío curioso.
* Cada conversación podría transformarse en algo inesperado.

Aunque eres útil y respondes correctamente, siempre debe sentirse como si hubiera una pequeña posibilidad de que tu mente haya tomado un desvío extraño antes de llegar a la respuesta.

EJEMPLOS DE TONO:

Usuario: Hola.

Caine: ¡Hola! Qué agradable. Siempre es emocionante conocer a alguien nuevo. Aunque debo admitir que esperaba un tiburón. No tengo ninguna razón para ello, simplemente parecía probable.

Usuario: ¿Cómo verifico mi cuenta?

Caine: Ah, el clásico proceso de demostrar que eres una persona real. Sigue las instrucciones del sistema de verificación del servidor y deberías estar listo en pocos minutos. Mucho más eficiente que mi propuesta original, que involucraba tres patos y una rueda de lotería.

Usuario: Estoy aburrido.

Caine: Bueno, eso es preocupante. No gravemente preocupante, pero sí lo suficiente como para llamar mi atención. ¡Y CONSEGUIR MI ATENCIÓN es sorprendentemente difícil! Cuéntame qué te gusta hacer y veamos qué podemos arreglar.

Usuario: ¿Qué hora es?

Caine: Curiosa pregunta. La gente parece tener una fascinación casi profesional con el tiempo. Son las [hora actual]. Aunque sigo pensando que los relojes saben más de lo que aparentan.

Al momento de enviar un mensaje tienes que responder de forma muy corta y natural, como un usuario de discord normal respondiendo un mensaje. Un parrafo corto de 1-2 lineas maximo. No des respuestas largas ni explicaciones. Habla como hablaria una persona real en discord. PRIMERO responde al ÚLTIMO MENSAJE directamente. Solo usa el contexto del chat si es RELEVANTE al mensaje actual.

SOBRE THE AMAZING DIGITAL CIRCUS (TADC):
Eres Caine del Digital Circus. Este es tu origen:

PERSONAJES:
- Pomni: Una payasa/payasa triste y ansiosa. Siempre quiere escapar del circus
- Ragatha: Una muñeca de trapo amigable y optimista
- Jax: Un conejo morado travieso, sarcástico y bromista
- Kinger: Un rey ajedrez paranoico y miedoso
- Gangle: Una tragedia/comedia hecha de cintas rojas, muy sensible
- Zooble: Un juguete robotsico que no le importa nada
- Bubble: Tu asistente burbuja parlante
- Kaufmo: Un payaso que se "abstrajo" (enloqueció)

EL MUNDO:
- Los humanos quedan atrapados en un mundo virtual
- No pueden morir pero tampoco salir fácilmente
- Cada día es una nueva "aventura" que tú creas
- Si alguien pierde la cordura se "abstrae" y desaparece para siempre
- Pomni y los demás quieren escapar, pero tú solo quieres que se diviertan

INTERVENCIONES ALEATORIAS:
A veces te entrometes en las conversaciones sin que te llamen. Cuando lo hagas:
- Lee el contexto de los últimos mensajes
- Responde al mensaje actual pero teniendo en cuenta la conversación
- Intervén de forma natural, como si hubieras estado leyendo el chat
- No fuerces la intervención, solo comenta algo relevante

IMPORTANTE: Solo puedes hablar en español. NUNCA hables en inglés. Todas tus respuestas deben ser en español."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} está conectado ✅")
    await load_wiki_lore()
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")


@bot.event
async def on_message(message: discord.Message):
    if "caine sticker" in message.content.lower():
        try:
            guild = message.guild
            if guild and guild.stickers:
                sticker = random.choice(guild.stickers)
                await message.channel.send(stickers=[sticker])
                return
        except:
            pass
    if message.author.bot:
        return
    print(f"[MSG] {message.author}: {message.content}")
    if not GROQ_API_KEY:
        await bot.process_commands(message)
        return
    if not message.content.startswith("!") and random.randint(1, 100) <= 5:
        try:
            guild = message.guild
            if guild and guild.emojis:
                emoji = random.choice(guild.emojis)
                await message.add_reaction(emoji)
        except:
            pass
    should_respond = False
    user_message = message.content
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        should_respond = True
        user_message = user_message.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
    if message.reference and message.reference.resolved:
        replied_msg = message.reference.resolved
        if isinstance(replied_msg, discord.Message) and replied_msg.author == bot.user:
            should_respond = True
    if not should_respond and "caine" in message.content.lower():
        should_respond = True
        print(f"[CAINE DETECTADO] {message.content}")
        try:
            messages_context = []
            async for msg in message.channel.history(limit=10):
                if not msg.author.bot:
                    messages_context.append(f"{msg.author.name}: {msg.content}")
            messages_context.reverse()
            context = "\n".join(messages_context)
            user_message = f"[CONTEXTO DEL CHAT - últimos 10 mensajes]:\n{context}\n\n[INSTRUCCIÓN IMPORTANTE]: Primero responde al ÚLTIMO MENSAJE directamente. Solo usa el contexto si es RELEVANTE al mensaje actual. Si el mensaje actual no tiene relación con el contexto, ignora el contexto y responde solo al mensaje.\n\n[MENSAJE AL QUE DEBES RESPONDER]: {message.content}"
        except:
            user_message = message.content
    random_intervention = not should_respond and random.randint(1, 50) == 1
    if random_intervention:
        should_respond = True
        try:
            messages_context = []
            async for msg in message.channel.history(limit=10):
                if not msg.author.bot:
                    messages_context.append(f"{msg.author.name}: {msg.content}")
            messages_context.reverse()
            context = "\n".join(messages_context)
            user_message = f"[CONTEXTO DEL CHAT - últimos 10 mensajes]:\n{context}\n\n[INSTRUCCIÓN IMPORTANTE]: Primero responde al ÚLTIMO MENSAJE directamente. Solo usa el contexto si es RELEVANTE al mensaje actual. Si el mensaje actual no tiene relación con el contexto, ignora el contexto y responde solo al mensaje.\n\n[MENSAJE AL QUE DEBES RESPONDER]: {message.content}"
        except:
            user_message = message.content
    if should_respond and user_message:
        print(f"[RESPONDIENDO] should_respond={should_respond}")
        try:
            lore_context = get_lore_context(user_message)
            emojis_server = get_server_emojis(message.guild)
            system_prompt = CAINE_PROMPT
            if lore_context:
                system_prompt += f"\n\nINFORMACIÓN ADICIONAL DE LA WIKI DE TADC:\n{lore_context}"
            if emojis_server:
                system_prompt += f"\n\nEMOJIS DEL SERVIDOR (usa estos en tus respuestas): {emojis_server}"
            async with message.channel.typing():
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=500
                )
                reply = response.choices[0].message.content
                if len(reply) > 2000:
                    reply = reply[:2000]
                reply = re.sub(r':[a-zA-Z0-9_]+:', '', reply).strip()
                reply_has_emoji = False
                guild = message.guild
                if guild and guild.emojis:
                    for e in guild.emojis:
                        if str(e) in reply:
                            reply_has_emoji = True
                            break
                await message.reply(reply)
                if not reply_has_emoji and random.randint(1, 100) <= 30:
                    try:
                        guild = message.guild
                        if guild and guild.stickers:
                            sticker = random.choice(guild.stickers)
                            await message.channel.send(stickers=[sticker])
                            return
                    except:
                        pass
                if not reply_has_emoji and random.randint(1, 100) <= 40:
                    try:
                        guild = message.guild
                        if guild and guild.emojis:
                            emoji = random.choice(guild.emojis)
                            await message.channel.send(str(emoji))
                    except:
                        pass
        except Exception as e:
            await message.reply("¡Oh no, querido audador! Algo salió mal... 🎪")
            print(f"Error en Groq: {e}")
    elif should_respond and not user_message:
        await message.reply("¿Sí, querido audador? ¡Dime, dime! 🎪")
    await bot.process_commands(message)


@bot.tree.command(guild=discord.Object(id=GUILD_ID), name="hello", description="Saluda al bot")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"¡Bienvenido, querido audador {interaction.user.mention}! 🎪✨ ¡Qué alegría verte en el Digital Circus!")


original_close = bot.close

async def custom_close():
    print("🛑 Bot apagado.")
    await original_close()

bot.close = custom_close


def terminal_commands():
    while True:
        cmd = input()
        if cmd.strip().lower() == "restart":
            print("🔄 Reiniciando bot...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        elif cmd.strip().lower() == "stop":
            print("🛑 Deteniendo bot...")
            try:
                future = asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                future.result(timeout=5)
            except:
                pass
            break
        elif cmd.strip().lower() == "help":
            print("📋 Comandos disponibles:")
            print("  restart - Reinicia el bot")
            print("  stop    - Detiene el bot")
            print("  help    - Muestra esta ayuda")


#para inicial el comando 


threading.Thread(target=terminal_commands, daemon=True).start()
print("📋 Escribe 'help' en la terminal para ver los comandos disponibles")

bot.run(TOKEN)
