from logging import disable
from discord import user
import discum
import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import random
import json
import sys, os
from datetime import datetime
import time
import pytz
import getopt
from config import *
from utils import *


UTC = pytz.utc # Get UTC timezone
Launch=True
Sattelite = discum.Client(token=USERTOKEN)
Sattelite.gateway.log = {"console":False, "file":False}
Sattelite.log = {"console":False, "file":False}
Bot = commands.Bot(command_prefix="$", case_insensitive=True)

Querying=False
LogLevel=2

List=[]
Counters=[]
Status=[]




# This function queries members userid's of which are included in the List, which are mostly janitors with are fetched by RIPBOZO function.
@Sattelite.gateway.command
def Boing(resp):
	if resp.event.ready_supplemental:
		Sattelite.gateway.checkGuildMembers(Guild, List, keep="all")
	if resp.event.guild_members_chunk and Sattelite.gateway.finishedGuildSearch(Guild, userIDs=List): 
		Sattelite.gateway.close()

def Log(type, log):
    types=["DEBUG", "LOG", "WARN", "ERROR", "FATAL"]
    CurTime=datetime.now(UTC)
    if (type>=LogLevel):
        try:
            with open(f"{logpath}", "a+", encoding="utf-8") as filewrite:
                filewrite.write(f"[{CurTime}] [{types[type]}]: {log}\n")
        except:
            Log(3, "Unable to open/save/write/whatever the file stated! Check path!")
            with open(f"{logpath}", "a+", encoding="utf-8") as filewrite:
                filewrite.write(f"[{CurTime}] [{types[type]}]: {log}\n")
        print(f"[{CurTime}] [{types[type]}]: {log}")




# The main function of the bot - this function queries the status of each member and outputs it if there are any differences.
async def CompareActivity():
	global Launch
	global NOINIT
	if len(List) == 0:
		Log(4, f"List is empty! Check role ids!")
		sys.exit(1)
	if (Launch == True): # Check if the script is booting
		for i in range(len(List)):
			what = Sattelite.gateway.session.guild(Guild).members[List[i]]
			# Returns a list, 0 - Username, 1 - Userid, 2 - Status, 3 - UTC timestamp
			tmp = await GetActivityString(what)
			Log(0, f"Queried {i}, got \"{tmp[0]} ({tmp[1]}) is {tmp[2]}\"")
			Status.append(tmp)
			await asyncio.sleep(0.6)
			await SendNotify(f"{tmp[0]} ({tmp[1]}) is {tmp[2]}")
		Launch=False
		try:
			await SendNotify(f"Cuckold monitoring is online.\nStarting heartbeat and tracking {len(Status)} users.")
		except IndexError:
			if NOINIT == False:
				Log(4, "Fetcher got 0 members! Check role ID's!")
			else:
				Log(1, "Running in NOINIT.")
		Log(0, "Initialised heartbeat")
	else:
		for i in range(len(List)):
			what = Sattelite.gateway.session.guild(Guild).members[List[i]]
			tmp = await GetActivityString(what)
			if tmp[2] != Status[i][2]:
				if Altdentping == True:
					if str(tmp[1]) == Altdentifier: # If altdentifier is triggered
						if str(tmp[2]) == "offline":
							Log(0, "Altdentifier ping triggered!")
							await SendNotify(f"<@&{Watchrole}>")
				Log(1, f"{tmp[0]} ({tmp[1]}) changed status to {tmp[2]}. Previously was {Status[i][2]}. {(datetime.now(UTC)-Status[i][3])} has elapsed.")
				Status[i] = tmp
				await SendNotify(f"{tmp[0]} ({tmp[1]}) is now {tmp[2]}")
			await asyncio.sleep(Heartbeat)

@Bot.event
async def on_ready():
	Log(1, "Bot started.")
	Log(0, f"Loaded {List}, its length is {len(List)}")
	if NOINIT == False:
		asyncio.get_event_loop().create_task(Ping())
		asyncio.get_event_loop().create_task(Pulse())
	else:
		await SendNotify("Running Amaryllis in NOINIT mode!")

async def SendNotify(message):
	channel = Bot.get_channel(BotChannel)
	await channel.send(message)

@Bot.command(name="Altdent")
async def ChangeAltdentping(ctx):
	if ctx.author.id == OWNERID:
		global Altdentping
		await SendNotify(f"Changed Altdentping to {not Altdentping}")
		Altdentping = not Altdentping


@Bot.command(name="heartbeat", brief="Pulse frequency")
async def ChangePulse(ctx, pulse):
	if ctx.author.id == OWNERID:
		Log(0, f"{ctx.author.id} called heartbeat. Argument passed is {pulse}")
		global Heartbeat
		if (pulse.isnumeric()):
			Heartbeat = int(pulse)
			await SendNotify(f"Changed pulse to {pulse}")
		else:
			Log(3, "Trying to pass an alpha character to heartbeat")

@Bot.command(name="kill")
async def Shutdown(ctx):
	if ctx.author.id == OWNERID:
		Log(1, f"Kill command passed, shutting down")
		await SendNotify("Достопримечательности ада манят свою аудиторию обратно.")
		sys.exit(0)

@Bot.command(name="total", brief="Fetches total online janitorial squad")
async def GetTotalOnline(ctx, mode="shallow"):
	global Querying
	if Querying == True:
		Log(2, f"{ctx.author.id} tried to call total function while lock is engaged.")
		await SendNotify("There is currently an API call in place. Not executing to avoid API ratelimits.")
		return
	Log(0, "Engaging lock")
	Querying=True
	Log(1, f"{ctx.author.id} called total in {mode} mode.")
	n=0
	misc=""
	if (mode == "shallow"):
		for i in Status:
			if i[2] != 'offline':
				n+=1
	elif (mode == "deep"):
		await SendNotify(f"Deep searching!\nThis will take approximately {len(List) * (3.5 + round(random.uniform(0.06, 0.3), 4))} seconds.")
		misc=[]
		for jannie in List:
			Log(0, f"Deep querying {jannie}")
			whatq = json.loads(Sattelite.searchMessages(Guild, authorID=jannie, limit=1).content.decode("utf-8"))
			try:
				distance = await CalculateDiff(whatq['messages'][0][0]['timestamp'])
			except IndexError:
				distance = 65565
			except KeyError:
				Log(3, "Halted deep querying due to a KeyError exception. Most likely this is a ratelimit error.")
				Log(3, f"Trace: {whatq}")
				await SendNotify(f"{whatq['message']} Halting execution.\nRetry after {whatq['retry_after']}")
			if distance < 60:
				Log(0, f"Found an active mod - {jannie}.")
				n+=1
				jan = await Bot.fetch_user(jannie)
				misc.append(f"{jan.name}#{jan.discriminator}")
			await asyncio.sleep(3.5)
	else:
		await SendNotify("Are you ok?")
	await SendNotify(f"{mode[:1].upper() + mode[1:]} search: Total online janitors: {n}. \n{misc}")
	Log(0, "Disengaging lock")
	Querying=False

async def CalculateDiff(timestamp):
	div = timestamp.split("T")
	Date = div[0]
	Time = div[1].split("+")[0]
	try:
		what = datetime.strptime(f"{Date} {Time}", "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=UTC) # Convert time to explicitly utc
	except ValueError:
		what = datetime.strptime(f"{Date} {Time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC) # Convert time to explicitly utc
	utcwhat = datetime.now(UTC) # Get current UTC time
	distance = int(( utcwhat - what).total_seconds() / 60) # Get difference
	Log(0, f"Comparing time: Given: {what}, compaing to {utcwhat}. Result in minutes is {distance}.")
	return distance

@Bot.command(name="rolelist")
async def GetRoleLists(ctx):
	RoleList = SortRoles(Sattelite.getGuildRoles(Guild).content.decode())
	with open("roles.txt", "w", encoding="utf-8") as file:
		for elem in RoleList:
			file.write(str(elem) + "\n")
	with open("roles.txt", "rb") as file:
		await ctx.channel.send(f"Role list for {Guild}", file=discord.File(file, "roles.txt"))
	os.remove("roles.txt")

@Bot.command(name="altteam")
async def TestInit(ctx):
	if ctx.author.id == OWNERID:
		RoleList = SortRoles(Sattelite.getGuildRoles(Guild).content.decode()) # This should be done beforehand and kept in memory


		MessageContent="Team composition:\n\n"
		RoleCounts = dict(json.loads(Sattelite.getRoleMemberCounts(Guild).content.decode()))
		Log(0, "Saved rolelist")
		Total=0
		for Role in RoleList:
			if Role['id'] in RoleIDList:
				MessageContent += f"{Role['name']}: {RoleCounts[Role['id']]}\n"
				Total+=RoleCounts[Role['id']]
		MessageContent+=f"There are {RoleCounts[MasterRole]} team members total."
		await SendNotify(MessageContent)


@Bot.command(name="lastmsg", brief="Displays date of last message")
async def LastMessage(ctx, userid):
	Log(1, f"{ctx.author.id} queried lastmsg on {userid}.")
	stringy=""
	whatq = json.loads(Sattelite.searchMessages(Guild, authorID=userid, limit=1).content.decode("utf-8"))
	try:
		distance = await CalculateDiff(whatq['messages'][0][0]['timestamp'])
		postdate=f"last posted at {whatq['messages'][0][0]['timestamp']}"
		Log(1, f"{userid}: Distance given: {distance}")
		#wtf
		if distance > 300:
			distance = int(distance/60)
			if distance > 48:
				if distance > 100000:
					stringy=f"This was very long ago."
				else:
					stringy=f"This was {int(distance/24)} days ago."
			else:
				stringy=f"This was {distance} hours ago."
		else:
			stringy=f"This was {distance} minutes ago."# Return how much minutes ago was the last message

		await SendNotify(f"{whatq['messages'][0][0]['author']['username']}#{whatq['messages'][0][0]['author']['discriminator']} {postdate}.\n{stringy}")
	except:
		await SendNotify(f"This user either does not exist, or has no messages.")

@Bot.command(name="dump", brief="Dumps information on a user.")
async def DumpMember(ctx, userid):
    Log(1, f"{ctx.author.id} called dump on {userid}")
    UserProfile = json.loads(Sattelite.getProfile(userid, guildID=Guild).content.decode())['guild_member']
    User = UserProfile['user']
    RoleList=[]
    RoleIDS = UserProfile['roles']
    try:
        for r in RoleIDS:
            for rn in range(len(RoleIDList)):
                if r == RoleIDList[rn]:
                    RoleList.append(RoleNameList[rn])
    except:
        Log(3, f"Dumping {userid} failed! Data: {UserProfile}, {RoleList}")

    await SendNotify(f"{User['username']}#{User['discriminator']} ({User['id']})\nNick: {UserProfile['nick']}\nJoined at: {UserProfile['joined_at']}\nTeam Roles: {RoleList}")

TeamMemberStorage=[]
async def Impulse(content, brief=False, invoked=True):
	global Querying
	Querying=True
	if brief:
		Querying=False
		return f"There are {json.loads(Sattelite.getRoleMemberCounts(Guild).content.decode())[MasterRole]} team members with the master role."
	else:
		Log(0, "Locked querying.")
		if invoked:
			await SendNotify(f"This will take a while, hold on.\nEstimated time of completion: {len(RoleIDList)*5} seconds.\nYou will be pinged whenever this finishes.")
		Tally=[]
		i=0
		diff=None
		for roleid,rolename in zip(RoleIDList,RoleNameList):
			MemberList = Filter(Sattelite.getRoleMemberIDs(Guild, roleid).content.decode())
			Tally+=MemberList
			try:
				diff=list(set(TeamMemberStorage[i]) ^ set(MemberList))
				if diff:
					tmp=f"{rolename}: \n"
					for d in diff:
						if d in TeamMemberStorage[i]: # If it's in cache but managed to vanish from MemberList - assume gone
							tmp+=f"{d} left.\n"
						elif d in MemberList:
							tmp+=f"{d} joined team.\n"
					TeamMemberStorage[i]=MemberList
					await SendNotify(f"<@&{Watchrole}>\n{tmp}")
			except IndexError:
				TeamMemberStorage.append(MemberList)
			MemberCount=len(MemberList)
			if invoked:
				content+=f"{rolename}: {MemberCount}\n"
			Log(0, f"Queried {rolename}, count is {MemberCount}")
			Log(0, f"List: {MemberList}")
			i+=1
			await asyncio.sleep(5)
	Querying=False
	Log(0, "Query lock disengaged.")
	if invoked == True and brief == False:
		TeamMembers=list(dict.fromkeys(Tally))
		FormattedTeamMembers=""
		for temp in TeamMembers:
			FormattedTeamMembers+=f"{temp}\n"
		try:
			with open(f"{teampath}", "w", encoding="utf-8") as filewrite:
				filewrite.write(FormattedTeamMembers)
		except:
			Log(3, "Unable to open/save/write/whatever the file stated to the path stated! Saving to root path instead!")
			with open(f"./team.txt", "w", encoding="utf-8") as filewrite:
				filewrite.write(FormattedTeamMembers)
		Log(0, f"Fetched a total of {len(TeamMembers)}, Member list uploaded to {resultlink}.")
		content+=f"\nThere are {len(TeamMembers)} team members total.\nMember list: {resultlink}"
		return content


@Bot.command(name="team", brief="Fetches current team composition.")
async def FORFREE(ctx, brief=None):
	Log(1, f"{ctx.author.id} called team")
	switch=False
	if brief != None:
		switch=True
	if (Querying == True):
		await SendNotify("There is a query currently in progress.")
		Log(3, f"Attempted to call a member role query while one is already running.\nCaller: {ctx.author.id}")
		return
	await SendNotify(await Impulse(f"<@{ctx.author.id}>\nMember structure:\n", switch))

@Bot.command(name="Janlist")
async def JanList(ctx):
	await SendNotify(List)

@Bot.command(name="loglevel")
async def ChangeLogLevel(ctx, level):
	global LogLevel
	if (ctx.author.id == OWNERID):
		Log(1, f"Changed log level to {level}")
		LogLevel = int(level)

@Bot.command(name="role")
async def RoleManage(ctx):
	role = get(ctx.guild.roles, id = int(Watchrole))
	if role in ctx.author.roles:
		Log(0, f"Removed role from {ctx.author.id}")
		await SendNotify(f"<@{ctx.author.id}>: Removed from teamwatch")
		await ctx.author.remove_roles(role)
	else:
		Log(0, f"Added role to {ctx.author.id}")
		await SendNotify(f"<@{ctx.author.id}>: Added to teamwatch")
		await ctx.author.add_roles(role)

@Bot.command(name="reboot")
async def reboot(ctx):
	if ctx.author.id == OWNERID:
		Log(1, "Reboot called")
		os.execv(sys.executable, ['python'] + sys.argv)

@Bot.command(name="resetlists")
async def resetlists(ctx):
	if ctx.author.id == OWNERID:
		Log(1, "Lists resetting")


@Bot.command(name="init")
async def kickstart(ctx):
	global NOINIT
	Log(0, f"{ctx.author.id} invoked init")
	if ctx.author.id == OWNERID:
		if (NOINIT == True):
			Log(0, "Kickstarting lists")
			NOINIT=False
			RIPBOZO()
			asyncio.get_event_loop().create_task(Ping())
			asyncio.get_event_loop().create_task(Pulse())
		else:
			Log(3, "Attempted to kickstart lists in INIT mode")
			await SendNotify("This command can be used only in NOINIT mode.")

async def Ping():
	while True:
		Sattelite.gateway.run()
		Log(0, "Heartbeat")
		await CompareActivity()

async def Pulse():
	while True:
		await asyncio.sleep(60*60)
		Log(0, "Impulse")
		await Impulse(None, brief=False, invoked=False)

NOINIT=False
# This function is in charge of fetching member id's of people that have moderator (janitorial) permissions.
# Depending on whether or not AUTO is set - it'll fetch all roles and find which roles are moderators, or use the defined roles in config to track.
def RIPBOZO():
	if NOINIT == False:
		global List
		List=[]
		Templist=[]
		UserIDList=[]
		if Auto == True:
			RoleList = SortRoles(Sattelite.getGuildRoles(Guild).content.decode())
			for i in range(len(RoleList)):
				if (CheckJanitorPerms(int(RoleList[i]["permissions"])) == True):
					Templist.append(RoleList[i]["id"])
		else:
			Templist = ModRoles
		for RoleId in Templist:
				Log(0, f"Getting UserID's for {RoleId}")
				UserIDList.append(Filter(Sattelite.getRoleMemberIDs(Guild, RoleId).content.decode()))
				time.sleep(5)
			# Flatten
		FlattenedUserIDList = [j for sub in UserIDList for j in sub]
			# Append to List
		[List.append(x) for x in FlattenedUserIDList if x not in List]
	else:
		Log(1, "Skipping RIPBOZO due to NOINIT")

#TODO: Rework the way arguments are passed
def Arguments(argv):
	global LogLevel
	global NOINIT
	try:
		opts, args = getopt.getopt(argv,"h:d:n:s:",["help", "debug", "noinit", "scum"])
	except getopt.GetoptError as goe:
		print("Invalid argument! Check documentation or pass '-h'.")
		print(goe)
		sys.exit(2)
	
	for opt, arg in opts:
		if arg.startswith('-'):
			opts.append((arg, '0'))
			arg = 0
		# discum log output will be changed only on boot
		# this in intentional so that the loglevel command only shows things Amaryllis is doing
		# if something regarding discum broke - chances are that bot commands are not going to work
		if opt in ("-s", "--scum"):
			Sattelite.gateway.log = {"console":True, "file":"gateway.log"}
			Sattelite.log = {"console":True, "file":"scum.log"}
			print("Logging Gateway/API calls")
		elif opt in ("-n", "--noinit"):
			NOINIT=True
			print("Noinit engaged.")
		elif opt in ("-d", "--debug"):
			LogLevel = int(arg)
	RIPBOZO() # Form a list of janitors
	print(f"Log Level is {LogLevel}")

def Init(args):
	Log(1, "Initializing")
	Arguments(args)
	Bot.run(BOTTOKEN)


if __name__ == "__main__":
	Init(sys.argv[1:])
#print(Status)