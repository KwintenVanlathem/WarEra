import discord
from discord.ext import commands, tasks
from config import config
from Database import Database
from psycopg2.extras import RealDictCursor

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
	try:
		synced = await bot.tree.sync()
		print(f"synced {len(synced)} commands")
		for command in synced:
			print(command.name)
	except Exception as e:
		print(e)

	print(f'We have the bot logged in as {bot.user}')
	
	if not notify_priority.is_running():
		notify_priority.start()

@bot.tree.command(name="sync")
async def createchannel(ctx: discord.Interaction, user_id: str):
	db = Database()
	db.syncDiscord(discordUser=ctx.user.id, userID=user_id)
	
	await ctx.response.send_message(f"User updated")

@tasks.loop(minutes=1)
async def notify_priority():
	sql = """
		SELECT 
			ARRAY_AGG(DISTINCT u.discord_id) AS discord_ids,
			e.name country,
			war.priority_end
		FROM war
		INNER JOIN country c ON c."countryID" IN (war.attacker_id, war.defender_id)
		INNER JOIN "user" u ON u.country_id = c."countryID" AND u.discord_id IS NOT NULL -- AND u.gov_role IN ('President', 'VP', 'MoD', 'MoFA')
		INNER JOIN country e ON e."countryID" IN (war.attacker_id, war.defender_id) AND e."countryID" != u.country_id
		WHERE (priority_end BETWEEN now() - interval '29 minutes' AND now() + interval '30 minutes' AND c."countryID" = war.has_priority)
		   OR (priority_end BETWEEN now() - interval  '1 minutes' AND now() - interval  '0 minutes' AND c."countryID" != war.has_priority)
		GROUP BY
			e."name",
			war.priority_end
	"""

	db = Database()
	with db.dbConnection.cursor(cursor_factory=RealDictCursor) as cur:
		cur.execute(sql)
		rows = cur.fetchall()
		for row in rows:
			mentions = " ".join(f"<@{discord_id}>" for discord_id in row["discord_ids"])
			message = (
				f"**{row['country']}**\n"
				f"Priority ends: <t:{int(row['priority_end'].timestamp())}:R>\n"
				f"{mentions}"
			)
			channel = await bot.fetch_channel(1541162666440134686)
			await channel.send(message)
		db.dbConnection.commit()

bot.run(config["discordToken"])