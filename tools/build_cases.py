"""Builds data/cases.json (100 episodes) — run once; the file is then the source of truth."""
import json, itertools

DOJ_PARK = "https://www.justice.gov/archives/opa/pr/north-korean-regime-backed-programmer-charged-conspiracy-conduct-multiple-cyber-attacks-and"
DOJ_3NK  = "https://www.justice.gov/usao-cdca/pr/3-north-korean-military-hackers-indicted-wide-ranging-scheme-commit-cyber-attacks-and"
FBI_SONY = "https://www.fbi.gov/news/press-releases/update-on-sony-investigation"
EUROPOL  = "https://www.europol.europa.eu/media-press/newsroom/news/mastermind-behind-eur-1-billion-cyber-bank-robbery-arrested-in-spain"
DOJ_YAHOO= "https://www.justice.gov/archives/opa/pr/us-charges-russian-fsb-officers-and-their-criminal-conspirators-hacking-yahoo-and-millions"
GONZ     = "https://www.justice.gov/archive/usao/nj/Press/files/pdffiles/2009/GonzIndictment.pdf"
CISA_NP  = "https://www.cisa.gov/news-events/alerts/2017/07/01/petya-ransomware"
CISA_ED  = "https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise-closed"
CISA_265 = "https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-265a"
CITIZEN  = "https://citizenlab.ca/research/poison-carp-tibetan-groups-targeted-with-1-click-mobile-exploits/"

# (key, title, year, category, actor, sources, origin, note)
F, A = "user_file", "added_replacement"
C = [
 ("sony","Sony Pictures hack — the Guardians of Peace",2014,"state","DPRK RGB / Lab 110 (Lazarus)",[FBI_SONY,DOJ_PARK],F,"Series opener, from the user's script"),
 ("darkseoul","DarkSeoul — the wiper that came before Sony",2013,"state","DPRK (Lazarus)",[FBI_SONY],F,""),
 ("bangladesh","Bangladesh Bank — the $81M SWIFT heist",2016,"finance","DPRK RGB",[DOJ_PARK],F,""),
 ("lazarus_banks","Lazarus and the billion-dollar bank campaign",2015,"finance","DPRK RGB",[DOJ_PARK],F,"Original case 6"),
 ("thaad","Phishing the THAAD contractors",2016,"espionage","DPRK Lab 110",[DOJ_PARK],F,"Original case 7"),
 ("wannacry","WannaCry — the worm that froze hospitals",2017,"ransomware","DPRK RGB",[DOJ_3NK],F,""),
 ("marinechain","Marine Chain — North Korea's fake crypto fleet",2018,"finance","DPRK RGB",[DOJ_3NK],F,""),
 ("applejeus","The trojanized crypto trading apps",2018,"finance","DPRK RGB",[DOJ_3NK],F,""),
 ("joanap","Joanap — the FBI maps a hidden botnet",2019,"state","DPRK",["https://www.justice.gov/archives/opa/pr/justice-department-announces-court-authorized-efforts-map-and-disrupt-botnet-used-north"],F,""),
 ("kejv","Chosun Expo — the front company behind the hacks",2018,"profile","Park Jin Hyok",["https://www.justice.gov/archives/opa/press-release/file/1092091/dl"],F,"Complaint affidavit"),
 ("carbanak","Carbanak — €1 billion without a gun",2013,"finance","Carbanak / Cobalt",[EUROPOL],F,""),
 ("cobalt_atm","Cobalt — midnight ATM jackpotting",2016,"finance","Cobalt group",[EUROPOL],F,""),
 ("yahoo","Yahoo — half a billion accounts and the FSB",2014,"breach","FSB officers + Belan + Baratov",[DOJ_YAHOO],F,""),
 ("baratov","Karim Baratov — the hacker-for-hire",2014,"profile","Karim Baratov",["https://www.justice.gov/archives/opa/pr/canadian-hacker-who-conspired-and-aided-russian-fsb-officers-pleads-guilty"],F,""),
 ("flyhook","Invita — the FBI's fake company sting",2000,"profile","Gorshkov & Ivanov",["https://www.justice.gov/archive/criminal/cybercrime/press-releases/2001/gorshkovconvict.htm"],F,""),
 ("uber","Uber's secret $100,000 bug bounty",2016,"breach","Uber / Joe Sullivan",[],F,"Original source link was a Mar-a-Lago PDF (wrong) — find DOJ Sullivan release"),
 ("stuxnet","Stuxnet — the first digital weapon",2010,"infra","State coalition",["https://www.cisa.gov/news-events/ics-advisories/icsa-10-238-01b"],F,""),
 ("duqu","Duqu — Stuxnet's silent twin",2011,"espionage","Unattributed state actor",[],F,""),
 ("night_dragon","Night Dragon — raiding the oil majors",2011,"espionage","China-based actors",[],F,""),
 ("shamoon","Shamoon — 30,000 Aramco computers wiped",2012,"infra","Cutting Sword of Justice",[],F,""),
 ("ukraine2015","Ukraine 2015 — the first hacker-made blackout",2015,"infra","Sandworm (GRU)",["https://nsarchive.gwu.edu/sites/default/files/documents/3891751/SANS-and-Electricity-Information-Sharing-and.pdf","https://cyote.inl.gov/content/uploads/24/2025/12/CyOTE-Case-Study_Ukraine-2015.pdf"],F,"Merges original 26-30"),
 ("industroyer","Industroyer — malware that speaks the grid's language",2016,"infra","Sandworm",["https://malpedia.caad.fkie.fraunhofer.de/details/win.industroyer"],F,""),
 ("notpetya","NotPetya — the $10 billion wiper",2017,"infra","Sandworm",[CISA_NP],F,""),
 ("triton","TRITON — attacking a refinery's safety system",2017,"infra","TsNIIKhM (TEMP.Veles)",["https://www.cisa.gov/sites/default/files/documents/MAR-17-352-01%20HatMan%20-%20Safety%20System%20Targeted%20Malware%20%28Update%20B%29.pdf"],F,""),
 ("dragonfly","Dragonfly — seven years inside energy plants",2011,"infra","FSB officers (Berserk Bear)",["https://www.cisa.gov/sites/default/files/publications/AA22-083A_TTPs_of_Indicted_State-Sponsored_Russian_Cyber_Actors_Targeting_the_Energy_Sector.pdf"],F,""),
 ("incontroller","INCONTROLLER — the sabotage toolkit caught early",2022,"infra","State APT",[CISA_265],F,""),
 ("volt","Volt Typhoon — hiding in America's water and power",2023,"infra","PRC (Volt Typhoon)",["https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a"],F,""),
 ("estonia","Estonia 2007 — a nation under digital siege",2007,"state","Hybrid / state-aligned",[],F,""),
 ("georgia","Georgia 2008 — cyberattacks beside tanks",2008,"state","State-aligned",[],F,""),
 ("moonlight","Moonlight Maze — the first APT",1996,"espionage","Russia-linked",[],F,""),
 ("titan","Titan Rain and Shawn Carpenter",2003,"espionage","PRC-linked",["https://content.time.com/time/press_releases/article/0,8599,1098911,00.html"],F,""),
 ("ghostnet","GhostNet — spying on 103 countries",2009,"espionage","China-based network",["https://citizenlab.ca/wp-content/uploads/2017/05/ghostnet.pdf"],F,""),
 ("aurora","Operation Aurora — Google vs. China",2009,"espionage","Elderwood group",["https://www.wired.com/2010/01/operation-aurora/"],F,"Merges original 45-51"),
 ("redoctober","Red October — five years in embassies",2007,"espionage","Russian-speaking actor",[],F,""),
 ("apt1","APT1 — the 12-story building in Shanghai",2006,"espionage","PLA Unit 61398",[],F,""),
 ("greatcannon","The Great Cannon",2015,"state","PRC network operators",[],F,""),
 ("poisoncarp","Poison Carp — spyware hunting Tibetans",2018,"espionage","Poison Carp",[CITIZEN],F,""),
 ("solarwinds","SolarWinds — the supply-chain masterplan",2019,"espionage","SVR (APT29)",[CISA_ED,"https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a"],F,"Merges original 57,60"),
 ("fireeye","FireEye — the hack that exposed SolarWinds",2020,"espionage","SVR (APT29)",[],F,""),
 ("supernova","SUPERNOVA — the second hacker in SolarWinds",2020,"espionage","Separate actor",[],F,""),
 ("heartland","Heartland — 130 million cards",2007,"finance","Albert Gonzalez ring",[GONZ],F,""),
 ("tjx","TJX — hackers in the parking lot",2005,"finance","Gonzalez & Watt",["https://www.justice.gov/archive/usao/ma/news/2010/April/TOEYsentPR.html"],F,""),
 ("hannaford","Hannaford — every checkout swipe copied",2007,"finance","Gonzalez ring",[GONZ],F,""),
 ("drinkman","Vladimir Drinkman — arrested on vacation",2012,"profile","Drinkman & Smilianets",["https://www.justice.gov/usao-nj/pr/russian-national-pleads-guilty-largest-known-data-breach-conspiracy-ever-charged"],F,""),
 ("newswire","The newswire hack — $30M from tomorrow's news",2010,"finance","Korchevsky et al.",["https://www.justice.gov/usao-nj/file/705921/dl?inline="],F,"Merges original 71-73"),
 ("capitalone","Capital One — the cloud engineer who bragged",2019,"breach","Paige Thompson",["https://www.justice.gov/usao-wdwa/united-states-v-paige-thompson"],F,""),
 ("lockbit","Operation Cronos — hacking LockBit",2024,"ransomware","LockBit",["https://www.nationalcrimeagency.gov.uk/news/nca-leads-international-investigation-targeting-worlds-most-harmful-ransomware-group"],F,""),
 ("changehc","Change Healthcare — America's billing system goes dark",2024,"ransomware","ALPHV/BlackCat",["https://www.hhs.gov/hipaa/for-professionals/special-topics/change-healthcare-cybersecurity-incident-frequently-asked-questions/index.html"],F,""),
 ("mckinnon","Gary McKinnon — the UFO hacker and the 10-year fight",2001,"profile","Gary McKinnon",["https://www.theguardian.com/world/2012/oct/16/gary-mckinnon-hacker-sparked-storm"],F,"Merges original 81-82"),
 ("lauri_love","Lauri Love vs. the United States",2013,"profile","Lauri Love",["https://www.theguardian.com/world/gary-mckinnon"],F,""),
 ("hbgary","HBGary Federal — the security firm that got hacked",2011,"breach","Anonymous",[],F,""),
 ("shadowbrokers","The Shadow Brokers — EternalBlue leaks",2016,"state","Shadow Brokers",[CISA_NP],F,"Merges original 89-90"),
 ("vulkan","Vulkan Files — Russia's private cyberwar contractor",2023,"state","NTC Vulkan (leak)",[],F,"Verify against Guardian/Spiegel/WaPo reporting"),
 # ---- replacements for weak/unverifiable/duplicate entries in the user's file ----
 ("morris","The Morris Worm",1988,"hacker","Robert T. Morris",[],A,""),
 ("mitnick","Kevin Mitnick — the most wanted hacker",1995,"profile","Kevin Mitnick",[],A,""),
 ("melissa","Melissa — the virus that jammed email",1999,"malware","David L. Smith",[],A,""),
 ("iloveyou","ILOVEYOU — the love letter worm",2000,"malware","Onel de Guzman (suspect)",[],A,""),
 ("mafiaboy","Mafiaboy takes down Yahoo and CNN",2000,"profile","'Mafiaboy'",[],A,""),
 ("codered","Code Red — the worm that hit the White House",2001,"malware","Unknown",[],A,""),
 ("slammer","SQL Slammer — 10 minutes to infect the internet",2003,"malware","Unknown",[],A,""),
 ("conficker","Conficker — the worm no one could kill",2008,"malware","Unknown",[],A,""),
 ("shadyrat","Operation Shady RAT",2011,"espionage","Unattributed",[],A,""),
 ("rsa","RSA SecurID — the breach behind the breach",2011,"espionage","APT",[],A,""),
 ("diginotar","DigiNotar — a fake Google certificate",2011,"breach","Iran-linked",[],A,""),
 ("psn","PlayStation Network — 77 million accounts",2011,"breach","Unknown",[],A,""),
 ("lulzsec","LulzSec — 50 days of chaos",2011,"profile","LulzSec",[],A,""),
 ("target","Target 2013 — through the air-conditioning vendor",2013,"breach","Crime group",[],A,""),
 ("heartbleed","Heartbleed — the bug that leaked the internet's memory",2014,"vuln","Bug (CVE-2014-0160)",[],A,"Narrative, no exploit detail"),
 ("mtgox","Mt. Gox — the missing 850,000 bitcoin",2014,"finance","Hackers / insiders",[],A,""),
 ("homedepot","Home Depot — 56 million cards",2014,"breach","Crime group",[],A,""),
 ("ashleymadison","Ashley Madison — the leak that ruined lives",2015,"breach","Impact Team",[],A,""),
 ("opm","OPM — 21 million security-clearance files",2015,"espionage","PRC-linked",[],A,""),
 ("anthem","Anthem — the largest health-insurer breach",2015,"breach","PRC-linked",[],A,""),
 ("mirai","Mirai — the botnet of cameras that broke the internet",2016,"malware","Paras Jha et al.",[],A,"Includes Dyn outage"),
 ("dnc","DNC hack — Fancy Bear and Cozy Bear",2016,"state","GRU / SVR",[],A,""),
 ("equifax","Equifax — 147 million people",2017,"breach","PLA members (indicted)",[],A,""),
 ("macron","MacronLeaks — hack and leak before the vote",2017,"state","APT28",[],A,""),
 ("vault7","Vault 7 — the CIA's leaked hacking arsenal",2017,"state","Joshua Schulte (convicted)",[],A,""),
 ("marriott","Marriott/Starwood — 500 million guests",2018,"breach","PRC-linked",[],A,""),
 ("norsk","Norsk Hydro vs. LockerGoga",2019,"ransomware","LockerGoga crew",[],A,""),
 ("baltimore","Baltimore — the city held hostage",2019,"ransomware","RobbinHood",[],A,""),
 ("twitter2020","Twitter 2020 — the Bitcoin scam on Obama and Musk",2020,"profile","Graham Ivan Clark",[],A,""),
 ("garmin","Garmin — the day the watches stopped",2020,"ransomware","Evil Corp (WastedLocker)",[],A,""),
 ("colonial","Colonial Pipeline — fuel panic",2021,"ransomware","DarkSide",[],A,""),
 ("jbs","JBS — the meat plant ransomware",2021,"ransomware","REvil",[],A,""),
 ("kaseya","Kaseya — 1,500 companies in one day",2021,"ransomware","REvil",[],A,""),
 ("hafnium","Exchange ProxyLogon — 30,000 servers at once",2021,"espionage","Hafnium (PRC)",[],A,""),
 ("log4shell","Log4Shell — the bug in everything",2021,"vuln","Bug (CVE-2021-44228)",[],A,"Narrative, no exploit detail"),
 ("polynetwork","Poly Network — the hacker who gave it back",2021,"finance","'Mr. White Hat'",[],A,""),
 ("lapsus","Lapsus$ — teenagers vs. Microsoft and Nvidia",2022,"profile","Lapsus$",[],A,""),
 ("ronin","Ronin Bridge — $620M and Axie Infinity",2022,"finance","DPRK (Lazarus)",[],A,""),
 ("conti_cr","Costa Rica — a nation declares emergency",2022,"ransomware","Conti",[],A,""),
 ("lastpass","LastPass — the vault that was stolen",2022,"breach","Unknown",[],A,""),
 ("mgm","MGM and Caesars — Scattered Spider",2023,"profile","Scattered Spider",[],A,""),
 ("moveit","MOVEit — mass extortion through a file-transfer tool",2023,"ransomware","Cl0p",[],A,""),
 ("snowflake","Snowflake — stolen logins, 165 customers",2024,"breach","UNC5537",[],A,""),
 ("salttyphoon","Salt Typhoon — inside US telecoms",2024,"espionage","PRC",[],A,""),
 ("bybit","Bybit — the $1.5 billion heist",2025,"finance","DPRK (Lazarus)",[],A,""),
 ("silkroad","Silk Road — the Dread Pirate Roberts",2013,"profile","Ross Ulbricht",[],A,""),
 ("alphabay","AlphaBay and Hansa — the dark-web double sting",2017,"profile","Law enforcement operation",[],A,""),
]
assert len(C) == 100, len(C)
assert len({c[0] for c in C}) == 100

# order: Sony first, then round-robin across categories so topics alternate
first, rest = C[0], C[1:]
cats = {}
for c in rest: cats.setdefault(c[3], []).append(c)
order = [first]
for grp in itertools.zip_longest(*cats.values()):
    order += [g for g in grp if g]
assert len(order) == 100

cases = []
for i, (k, t, y, cat, actor, src, origin, note) in enumerate(order, 1):
    cases.append({"episode": i, "key": k, "title": t, "year": y, "category": cat, "actor": actor,
                  "sources_from_user_file": src, "origin": origin, "note": note, "status": "pending"})
json.dump(cases, open("data/cases.json", "w"), indent=1, ensure_ascii=False)
print(len(cases), "cases;", sum(c["origin"]==F for c in cases), "from user file,", sum(c["origin"]==A for c in cases), "added")
for c in cases[:12]: print(c["episode"], c["title"], c["year"], c["category"])
