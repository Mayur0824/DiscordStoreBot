import aiosqlite
import os

DB_PATH = 'database/store_bot.db'

async def init_db():
    if not os.path.exists('database'):
        os.makedirs('database')
        
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS autoresponder (
                trigger_word TEXT PRIMARY KEY,
                response_text TEXT,
                image_url TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS g2g_scraped (
                offer_id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS g2g_config (
                guild_id INTEGER PRIMARY KEY,
                public_channel_id INTEGER,
                admin_channel_id INTEGER
            )
        ''')
        await db.commit()

async def add_autoresponder(trigger: str, response_text: str | None = None, image_url: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO autoresponder (trigger_word, response_text, image_url)
            VALUES (?, ?, ?)
        ''', (trigger, response_text, image_url))
        await db.commit()

async def get_autoresponder(trigger: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT response_text, image_url FROM autoresponder WHERE trigger_word = ?', (trigger,)) as cursor:
            return await cursor.fetchone()

async def delete_autoresponder(trigger: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM autoresponder WHERE trigger_word = ?', (trigger,))
        await db.commit()

async def get_all_autoresponders():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT trigger_word FROM autoresponder') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# --- Warning Functions ---
async def add_warning(user_id: int, guild_id: int, admin_id: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO warnings (user_id, guild_id, admin_id, reason)
            VALUES (?, ?, ?, ?)
        ''', (user_id, guild_id, admin_id, reason))
        await db.commit()

async def get_user_warnings(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT admin_id, reason, timestamp FROM warnings 
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id)) as cursor:
            return await cursor.fetchall()

# --- G2G Scraper Functions ---
async def is_offer_scraped(offer_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT 1 FROM g2g_scraped WHERE offer_id = ?', (offer_id,)) as cursor:
            return await cursor.fetchone() is not None

async def add_scraped_offer(offer_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO g2g_scraped (offer_id) VALUES (?)', (offer_id,))
        await db.commit()

async def get_g2g_config(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT public_channel_id, admin_channel_id FROM g2g_config WHERE guild_id = ?', (guild_id,)) as cursor:
            return await cursor.fetchone()

async def set_g2g_config(guild_id: int, public_channel_id: int | None = None, admin_channel_id: int | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT public_channel_id, admin_channel_id FROM g2g_config WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
        
        if row:
            new_pub = public_channel_id if public_channel_id is not None else row[0]
            new_adm = admin_channel_id if admin_channel_id is not None else row[1]
            await db.execute('UPDATE g2g_config SET public_channel_id = ?, admin_channel_id = ? WHERE guild_id = ?', (new_pub, new_adm, guild_id))
        else:
            await db.execute('INSERT INTO g2g_config (guild_id, public_channel_id, admin_channel_id) VALUES (?, ?, ?)', (guild_id, public_channel_id, admin_channel_id))
        await db.commit()
