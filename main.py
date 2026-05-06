#准备工作
import requests#把requests工具从python里面给我拿出来，后面要用它处理网络请求，是给常用工具。
from web3 import Web3#把web3工具从web3库里给我拿出来，后面要用它连接以太坊主网，是web3编程常用工具。

import json#把json翻译官工具从python里拿出来，用来把python得到的数据翻译成文本文件储存起来，也可以把文本文件翻译成可以让python直接使用的数据。
import os#把os工具从python里拿出来，用来直接和计算机系统交流的工具，在生成数据的时候用于判断存放数据的文件是否存在，判断以后引导后续逻辑操作，这是把关人。
from datetime import datetime, timedelta#把datetime工具从datetime工具箱里拿出来，用来获取实时时间。timedelta是时间差计算工具，配合时间戳查找历史数据。
import pytz#把pytz工具从pytz库里拿出来，用来处理时区转换，确保在Railway服务器上使用的是上海东八区时间。
shanghai_tz = pytz.timezone('Asia/Shanghai')#定义上海时区，后面所有datetime.now()都会用这个时区。
from openai import OpenAI#把openai工具从openai库里拿出来，后面要用它调用gpt的api接口，是引入gpt到脚本工作的常用工具。
import schedule#把schedule工具从schedule库里拿出来，用来设置定时任务，让程序每小时自动运行一次。
import time#把time工具从python里拿出来，配合schedule使用，让程序在等待下次执行时保持运行状态。

from dotenv import load_dotenv#把调用dotenv工具从python里拿出来，用来调用.env文件里的密钥记录，写入到代码里相应位置。
load_dotenv()  #执行读取.env文件的指令。

def find_closest(history, target_time, max_diff_hours=0.5):#定义一个函数用来判断是不是离目标时间点最接近的记录，里面的参数是形式参数，实际上最后面都会用到，现在先挖好坑放在这里等着填充进来。
    result = min(history, key=lambda r: abs(#history是外面后面的数据记录列表，对于history1
        (datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S") - target_time).total_seconds()#target_time对应target_today_8am
    ))#先找出最接近目标时间的那条数据。
    diff = abs((datetime.strptime(result["timestamp"], "%Y-%m-%d %H:%M:%S") - target_time).total_seconds())#算出这条数据和目标时间差了多少秒。
    if diff <= max_diff_hours * 3600:#前面写死了max_diff_hour为0.5，这里表示里目标时间最近的这条记录有0.5*3600秒的差距
        return result#如果在这个差距以内，这条数据还是相对还是有效的，把这条数据返回使用。
    else:
        return None#指超过了这个时间差距，说明参考意义不大，直接就返回空集none。

def call_gpt(messages, model="gpt-5.5"):#我们定义一个叫call_gpt的函数，这个函数定义以后，后面需要调用gpt分析的地方就不用重复写一大堆api参数，直接引用call_gpt这个短代码就可以了。
    api_configs = [#设置了三个api接口用来备用，有失效了用备用继续完成任务，程序不会崩溃。我们把三个api接口写成一个列表，然后装进字典api_configs里面，方便后面引用。
        {"api_key": os.getenv("GPT_API_KEY_1"), "base_url": os.getenv("GPT_BASE_URL_1")},
        {"api_key": os.getenv("GPT_API_KEY_2"), "base_url": os.getenv("GPT_BASE_URL_2")},
        {"api_key": os.getenv("GPT_API_KEY_3"), "base_url": os.getenv("GPT_BASE_URL_3")},  
    ]
    for config in api_configs:#用for/in循环，把字典里每个列表参数一个一个拿出来做同样的一个任务，直到调用成功就进行return返回结果。
        try:#try/except语法很有意思，相当于try里面的内容如果正常运行了，就不继续运行except里面的内容，如果try里面的内容运行失败了，就继续运行except里面的内容。表示一种备用选择，而不是try里面都调用失败就把程序搞崩溃，用except里面的步骤来当失败托底，就是说失败了我们就跳过这个事情别纠结这个程序运行，继续往下面走就好。
            client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])#client是客户端的意思，相当于我们用OpenAI工具连接api接口，api_key是api接口的密钥，base_url是api接口的地址，我们把api_key和base_url写成一个字典config，然后装进api_configs里面，方便后面引用。
            response = client.chat.completions.create(#连接api的具体步骤。
                model=model,
                messages=messages
            )
            print("✅ GPT调用成功")
            return response.choices[0].message.content#直接返回api连接跑通后返回的结果，选择用return是为了后续几处引用这个结果，所以用return返回结果。
        except Exception as e:#这个是当try里面的步骤失败了，提醒失败原因的语法，Exception代表所有错误类型的集合，把遇到的错误类型定义叫e，后面打印失败原因的时候直接引用。
            print(f"⚠️ GPT调用失败：{e}，尝试备用接口...")
    print("❌ 所有GPT接口都失败了，跳过AI分析")#代表三个接口都没连上的情况。
    return None#三个接口都没连上直接把返回的结果定义为空集，不直接用exit退出是因为这个步骤运行不了，后面的步骤还有继续运行的必要，继续进行下面的步骤就好。

rpc_list=[#定义一个叫rpc_list的字典，把几个获取主网连接的api接口写进去，因为连接主网是这个程序的基础步骤，如果主网都连不上就没必要运行这个程序了。
        os.getenv("RPC_1"),
        os.getenv("RPC_2"),
        os.getenv("RPC_3"),
        ]

def send_tg(message):#定义发送Telegram消息的函数，后面需要发消息的地方直接调用这个函数就好。
    token = os.getenv("TG_BOT_TOKEN")#从.env里拿到bot的token密钥。
    chat_id = os.getenv("TG_CHAT_ID")#从.env里拿到你的chat_id。
    if not token or not chat_id:#如果token或chat_id没有填，就跳过发送，不让程序崩溃。
        print("⚠️ TG_BOT_TOKEN或TG_CHAT_ID未配置，跳过TG推送")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
        print("✅ TG消息发送成功")
    except Exception as e:
        print(f"⚠️ TG消息发送失败：{e}")


def job():#把所有业务逻辑包进job函数，schedule每小时调用一次这个函数。
    print(f"\n{'='*30} 开始新一轮运行 {datetime.now(tz=shanghai_tz).strftime('%Y-%m-%d %H:%M:%S')} {'='*30}")

    w3 = None#先定义变量w3为空集，先安个牌坊在这里，上面先不刻字，具体刻不刻按照try的运行说话，如果try成功运行，那就把刻的内容把none替换掉。
    for rpc in rpc_list:#用for/in循环把字典里的每个api挨个按所需尝试与主网连接。
        try:#开始按写法尝试程序运行步骤
            w3_temp = Web3(Web3.HTTPProvider(rpc))#给尝试与主网连接这个过程取名w3_temp，因为连接主网是否成功不会直接返回结果反馈，
            if w3_temp.is_connected():#is_connected是web3库自带的判断是否连接成功的特殊写法，如果连接成功就执行下面步骤，如果不成功直接跳到except执行。
                w3 = w3_temp#这里表示w3_temp是在主网连接成功的情况下，我们用刻字内容把none替换了。
                print(f"✅ 主网连接成功：{rpc}")#打印出连接成功的api接口地址。
                break#表示跳出for/in循环，因为已经找到连接成功的api接口了，不用再继续尝试了。
        except Exception as e:#没连上主网。
            print(f"⚠️ 连接失败：{rpc}，原因：{e}，尝试下一个...")#表示连接失败了，打印出失败的原因。
    if w3 is None:#如果w3变量还是空集，就是说没有连接成功，就执行以下步骤。
        print("❌ 所有主网节点连接失败，跳过本次运行")#表示所有api接口都连接失败了，打印出失败的原因。
        return#在job函数里用return代替exit，表示跳过本次运行，等下一个小时再试，不会让整个程序崩溃退出。

    #在主网链上拿到steth代币的总供应量
    STETH_ADDRESS="0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"#STETH代币的合约部署地址就是后面的十六进制代码，后面代码里输入STETH_ADDRESS就是调用这个合约地址干活。这串地址是在以太坊主网世界里独一无二的steth的身份证号码，身份识别码，你有他就能到庞大的主网里面找到他
    ABI_connect = [
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]#ABI相当于是这个合约开发者给外面的人写的一本说明书，方便外面的人用这个说明书直接和合约对话，因为外面的人是不能直接看懂和读写合约的，所以需要借助这个翻译说明书。ABI指令是官方合约创始人规定好了模板和内容的，我们如果要调用直接就去复制粘贴就能得到你想要的数据。而且erc20协议的代币都用totalsupply这个ABI通用指令来查询总供应量。所以这里我们直接调用就好了
    total_supply_eth=None#我们先提前定义这个变量为空集，就是说先默认他try里面的程序失败，先叠个甲后面备用。
    try:#里面隐含逻辑，如果try里面程序运行成功，这个none空集就被替换成成功后获取的这个数据。
        contract=w3.eth.contract(address=STETH_ADDRESS,abi=ABI_connect)#相当于连接abi这个过程定义为contract，到时方便输入contract就可以随时调用这个状态。w3.eth.contract表示我们随时通过alchemy这个中间人进入主网去干事情，（address=STETH_ADDRESS,abi=ABI_connect)表示我们去找到身份证号（合约代码）对应上的这个人，然后用能让他听得懂的指令ABI来拿到我们的信息。整个过程就是去主网找到币的合约拿到总供应量过程
        total_supply=contract.functions.totalSupply().call()#连接好abi以后用total_supply功能执行查总供应量任务，也用total_supply定义查总供应量的函数名字。contract属于一个大菜单表示整个智能合约，包含了function整个功能菜单，total_Supply()就是属于功能菜单里面要求调用总供应量的指令，call（）意思是直接执行这个指令拿出结果来，而不只是看结果，而是直接拿结果使用结果。
        total_supply_eth =total_supply/10**18#因为从以太坊上返回的总供应量的数据是按以太坊原生代币的的最小单位wei计数的，因为1eth=10**18wei，所以我们要除以10**18就知道有多少个steth代币，我们把这个结果的名字定义为total_supply_eth ，方便后面引用。
        print(f"✅ stETH总供应量：{total_supply_eth:.2f} ETH")#输出数据结果的单位就是是用eth计数的eth数量，保留两位小数。
    except Exception as e:#这里也隐含一个逻辑，如果是try里面不成功，变量还是none没变，只是说后续没写出来给我们看而已。
        print(f"⚠️ 获取总供应量失败：{e}，跳过本次运行")#表示try里面运行失败了，给我们报错，这里还是total_supply_eth=None
        return#总供应量都没拿到，跳过本次运行，等下一个小时再试。



    #在chainlink预言机上拿到eth/usd交易对的最新实时价格
    CHAINLINK_ADDRESS="0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"#这是eth/usd交易对在chainlink预言机上的合约地址，要调用就需要找到他的这串身份证号
    ABI_CHAINLINK = [{
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]#这里调用的也是预言机官方给的ABI，使用的latestRoundData这个功能来查询调用eth/usd交易对的现价，这里用usd是使用了法币美元做单位，因为如果选usdt或usdc也可以，但是可能会遇到稳定币可能极端脱钩那种情况，使用直接用法币比较客观。
    eth_price_chainlink = None#先定义好它为空集，至于后面是不是空集就看在预言机上有没有拿到。
    try:#先在try里面试试，拿到了就把none赶走，让新人接替none的位置。
        chainlink = w3.eth.contract(address=CHAINLINK_ADDRESS, abi=ABI_CHAINLINK)#同理和上面调用totalsupply功能一样，这里调用最新价格，固定模板就这样写，因为和上面的定义有很多共同使用的如w3.eth.contract一样的变量都是同一个变量多次使用，所以不用重复定义名字就可以直接拿来使用。
        data=chainlink.functions.latestRoundData().call()#直接调用官方提供的查询最新价格功能的latestrounddata函数和上面的totalsupply用法类似我就不赘述了，获得的数据变量取名叫data，方便后面使用，实际上会获得五个数据：轮次ID, 价格, 开始时间, 更新时间, 轮次，但是等下我们只需要价格
        eth_price_chainlink=data[1]/10**8#data[1]表示选择的列表里的第二个数据。因为官方规定，主网上获得的价格需要结果处理，要除以10**8才能拿到平时我们看到的eth价格，主要是以太坊上的数据都是整数，不以小数形式出现，所有都要经过decimal精度换算和前面除以10**18一个原理
        print(f"✅ Chainlink ETH价格：${eth_price_chainlink:.2f}")#得到了eth/usd交易对在chainlink预言机上的最新实时价格，保留两位小数。
    except Exception as e:#表示try里面失败了，none这小子继续留下来吧，现在进行报错环节。
        print(f"⚠️ 获取Chainlink价格失败：{e}，尝试下一个...")#打印没有拿到预言机价格的原因给我们我们看。

    #在pyth预言机上拿到eth/usd交易对的最新价格
    PYTH_ADDRESS = "0x4305FB66699C3B2702D4d05CF36551390A4c69C6"#也在pyth预言机上找到eth的价格在主网的合约地址，找到身份证号码为了找他沟通拿数据，这里是在官方网站找到的
    ABI_PYTH = [{
        "inputs": [
            {"internalType": "bytes32", "name": "id", "type": "bytes32"}
        ],
        "name": "getPriceUnsafe",
        "outputs": [
            {"components": [
                {"internalType": "int64", "name": "price", "type": "int64"},
                {"internalType": "uint64", "name": "conf", "type": "uint64"},
                {"internalType": "int32", "name": "expo", "type": "int32"},
                {"internalType": "uint256", "name": "publishTime", "type": "uint256"}
            ],
            "internalType": "struct PythStructs.Price",
            "name": "price",
            "type": "tuple"}
        ],
        "stateMutability": "view",
        "type": "function"
    }]#依然是调用官方给的ABI指令，pyth预言机用getpriceunsafe功能去查询实时价格，但是需要输入eth/usd的feedid，我去官网查了但是官网崩了我直接使用了ai给我的，这一步和chainlink不同，chainlink不用传参数，但是pyth需要输入ETH_USD_ID这个参数才能返回数据拿到价格
    ETH_USD_ID = "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace"#这个就是ai直接给的ETH_USD_ID地址，等下必须用到
    eth_price_pyth=None#老规矩，可以不用但是不能没有。
    try:#试一下能不能拿到价格
        pyth = w3.eth.contract(address=PYTH_ADDRESS, abi=ABI_PYTH)#带上abi用身份证号码找到主网上的合约拿数据，套用上面类似的模板，固定写法，直接调用就好
        data = pyth.functions.getPriceUnsafe(ETH_USD_ID).call()#定义拿到返回的数据为data，方便后面引用
        eth_price_pyth = data[0] * (10**data[2])#拿到的数据老规矩，[0]就表示列表里面的第一个数据，然后要按他的要求经过精度处理，[2]就是列表里面的第三个数据，表示精度，然后相乘就是拿到处理后的价格
        print(f"✅ Pyth ETH价格：${eth_price_pyth}")#提醒我们成功拿到价格了。
    except Exception as e:#还是没拿到，还是让none这小子呆着吧。
        print(f"⚠️ Pyth获取失败：{e}")#打印为啥没拿到价格的原因。
    #以下是价格替代的代码实现过程，这里面我们前面几处定义的none就派上了用场，画龙点睛之笔来了。
    if eth_price_chainlink is None and eth_price_pyth is None:#这下子两个预言机都没拿到价格
        print("❌ 两个预言机都挂了，跳过本次运行")#提醒我们失败了
        return#价格拿不到跳过本次运行，等下一个小时再试。
    elif eth_price_chainlink is None:#chainlink预言机没拿到，但是pyth拿到了
        eth_price_chainlink = eth_price_pyth#为了后面程序能够继续运行下去，就把pyth预言机拿到的结果赋值给chainlink预言机吧，py价chain用。
        print("⚠️ Chainlink不可用，用Pyth价格替代")#告诉我们那个失败了，换成了那个渠道。
    elif eth_price_pyth is None:#这下子pyth预言机没拿到价格，但是chainlink拿到了。
        eth_price_pyth = eth_price_chainlink#为了后面程序能够继续运行下去，就把chainlink预言机拿到的结果赋值给pyth预言机吧，chain价py用。
        print("⚠️ Pyth不可用，用Chainlink价格替代")#告诉我们那个失败了，换成了那个渠道。

    #计算tvl_chainlink
    steth_tvl_chainlink=eth_price_chainlink*total_supply_eth#把上面我们在链上通过alchemy拿到的steth的总锁仓量*预言机上拿到的eth/usd币对的实时最新价格的积就是tvl_chainlink
    print(steth_tvl_chainlink)#打印出来tvl_chainlink的结果就是chainlink预言机计算出来的steth的美元价值总额，就是所谓tvl。

    #计算tvl_pyth
    steth_tvl_pyth=eth_price_pyth*total_supply_eth#用pyth预言机拿到的价格乘以我们在主网上拿到的steth锁仓数量的积就是tvl_pyth
    print(steth_tvl_pyth)#打印出来tvl_pyth的结果就是pyth预言机计算出来的steth的美元价值总额，就是所谓tvl。




    #接下来是查询金库除steth外的其他资产总额获取过程
    url_llama = "https://api.llama.fi/protocol/lido"#这是直接调用的defillama的lido金库的api，里面存了金库的详细数据，锁仓有哪些代币，每个代币的余额是多少，每个代币的价格是多少，可以拿到金库的详细数据，方便大家直接调取数据。
    response = requests.get(url_llama,timeout=10)#用requests工具调用网址api拿到数据，把数据存起来以response命名，这个过程就是请求过程，response就是拿到的回应表示调取到的数据结果。
    data = response.json()#把上面调取到的数据通过json工具转换成json格式让python读取，这个转换好的json格式的数据用data命名变量。
    tokens_usd = data["tokensInUsd"][-1]["tokens"]#在返回的转换好的data数据里面找到"tokeninusd"字段关键字，在这个字段里面[-1]表示defillama拉取的最新的一条价格数据，["tokens"]表示在最新的一条数据里取出锁仓代币价值，这一步就是拿到了金库的详细数据。
    print(tokens_usd)#打印出来lido金库里面所有锁仓代币分别的价值 ，拿到的数据结构是一个字典，字典里面是很多组一一对应的数据，是这种格式：{'WETH': 168433641.52, 'USDC': 110231981.14, 'USDT': 108325417.26, 'WBTC': 3331058.46, 'WMATIC': 13113611.53, 'DOT': 330385.56, 'KSM': 253242.32, 'SOL': 210154.31}

    #计算other_tvl_第一种方法，weth就是steth包裹的eth，所以不算，其他代币都算。这种做法就是把字典里面排除weth以后的属于所有代币的价值用for/in循环把剩余所有代币的价值都累加起来。这个办法最开始我没太明白但是后来搞清楚了来龙去脉。
    other_tvl_第一种方法 = 0#定义除开了steth以外的其他代币的tvl起始值定义为0，方便后面累加。
    for k, v in tokens_usd.items():#用for循环把字典tokens_usd里面一一对应拆开，得到很多组一一对应的key和value。
        if k != "WETH":#如果key不等于WETH，就累加value，因为WETH是steth包裹的，算了就会重复，所以不加。
            other_tvl_第一种方法 += v#累加value，因为value就是代币的价值，所以累加就是累加代币的价值。
    print(other_tvl_第一种方法)#打印出来累加的结果

    #计算other_tvl_第二种方法，这种做法就是直接在字典里面找到WMATIC、DOT、KSM、SOL代币的价值，然后相加就是除开了steth以外的其他代币的tvl总和。这个办法是最简单最直观的做法，但是缺点是不够智能，如果金库里新增加了代币，这个办法就不行了，需要手动修改代码。
    WMATIC_TVL=tokens_usd["WMATIC"]#在锁仓代币价值字典里面找到WMATIC代币的价值，取名叫WMATIC_TVL，方便后面引用。
    DOT_TVL=tokens_usd["DOT"]#在锁仓代币价值字典里面找到DOT代币的价值，取名叫DOT_TVL，方便后面引用。
    KSM_TVL=tokens_usd["KSM"]#在锁仓代币价值字典里面找到KSM代币的价值，取名叫KSM_TVL，方便后面引用。
    SOL_TVL=tokens_usd["SOL"]#在锁仓代币价值字典里面找到SOL代币的价值，取名叫SOL_TVL，方便后面引用。
    other_tvl_第二种方法=WMATIC_TVL+DOT_TVL+KSM_TVL+SOL_TVL#除开了steth以外的其他代币的tvl总和
    print(other_tvl_第二种方法)#打印出来除开了steth以外的其他代币的tvl总和

    #total_tvl_CHAINLINK结果
    total_tvl_CHAINLINK=steth_tvl_chainlink+other_tvl_第一种方法#参考预言机为chainlink得出的总锁仓量
    print(total_tvl_CHAINLINK)#打印出来的结果

    #total_tvl_pyth结果
    total_tvl_pyth=steth_tvl_pyth+other_tvl_第一种方法#参考预言机为pyth得出的总锁仓量
    print(total_tvl_pyth)#打印出来的结果

    #在defillama的api上拿到金库里所有锁仓代币的总锁仓量作为与上面两种方法计算的参考对比 
    url_llama = "https://api.llama.fi/protocol/lido"
    response = requests.get(url_llama,timeout=10)
    data = response.json()
    Defillama_tvl = data["tvl"][-1]["totalLiquidityUSD"]


    #以下是获取金库当日八点apr的代码
    # 调用Lido官方API拿到APR
    hour = datetime.now(tz=shanghai_tz).hour#获取当前具体小时
    lido_apr = None#先假装没有拿到数据，叠个甲先。
    apr_onchain = None#先假装没有拿到数据，叠个甲先。

    if hour == 8:#在八点才会运行以下程序
        url_lido_apr = "https://eth-api.lido.fi/v1/protocol/steth/apr/last"#到lido官网调取每天apr，这里是调取接口网址，用 url_lido_apr。
        response_lido_apr = requests.get(url_lido_apr,timeout=10)#实施调取apr这个步骤，用response_lido_apr变量命名。
        data_lido_apr = response_lido_apr.json()#用json翻译官去翻译返回来的数据，用data_lido_apr变量命名。
        lido_apr = data_lido_apr["data"]["apr"]#在返回来翻译过的数据里先去"data"里取值，然后在取到的值里把"apr"取值出来，就拿到官网提取的每日apr数据结果。
        print(f"Lido官方API APR：{lido_apr:.4f}%")#打印出来官网取到的具体每日apr是多少给我们反馈。

    #以下是用链上计算apr的方法，在同样前提都是在8点运行以下步骤。
        latest_block = w3.eth.block_number#首先拿到程序运行这个时候的最近区块号。
        event_signature = "0x" + w3.keccak(text="TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)").hex()#用固定格式带着这个事件的身份证用keccak去解码这个事件出来。
        flock_block = latest_block - 20000#用最近这个区块号减去20000个区块，就得到上一次分发收益时的区块附近，因为一个星期大概会新增50000个区块左右，我就折半缩小了范围，更节省资源。

        logs = w3.eth.get_logs({#现在去读取这间隔的区块里，这个发放收益的日志记录。
            "fromBlock": flock_block,
            "toBlock": latest_block,
            "address": STETH_ADDRESS,
            "topics": [event_signature]
        })

        log = logs[-1]# 取日志里最近的1条rebase记录。
        data = log["data"]#取出这一条里面的data字段的对应值出来。
        values = [int.from_bytes(data[i:i+32], "big") for i in range(0, len(data), 32)]#把data返回来的数据从二进制转换成32个字节的数字列表，让我们可以读取。

        timeElapsed     = values[0]# 距离上次rebase过了多少秒
        preTotalShares  = values[1]# rebase前的总份额
        preTotalEther   = values[2]# rebase前的总ETH
        postTotalShares = values[3]# rebase后的总份额
        postTotalEther  = values[4]# rebase后的总ETH

        pre_share_price  = preTotalEther / preTotalShares# rebase前每份额值多少ETH
        post_share_price = postTotalEther / postTotalShares# rebase后每份额值多少ETH

        apr_onchain = (post_share_price - pre_share_price) / pre_share_price * (365 * 24 * 3600 / timeElapsed)#(post - pre) / pre → 这次rebase涨了百分之几 * (365 * 24 * 3600 / timeElapsed) → 按这个速度涨一年是多少，就是年化 365 * 24 * 3600 是一年的总秒数，除以这次rebase间隔的秒数，就知道一年能rebase多少次，乘起来就是年化。
          
        print(f"链上最近1次rebase APR：{apr_onchain*100:.4f}%")#打印出通过链上计算出的apr具体值。

        apr_diff = abs(lido_apr - apr_onchain * 100)#取绝对值得出的差距结果不会出现复数的情况，如果出现了负数下面的条件永远触发不了，与设计理念相悖。

        if apr_diff > 1:#如果绝对值差距大于百分之一，进行以下步骤。
            print(f"🔴 红色预警：官方APR {lido_apr:.4f}% vs 链上APR {apr_onchain*100:.4f}%，差距 {apr_diff:.4f}%，官方数据疑似造假！以链上数据为准。")
        elif apr_diff > 0.5:#如果绝对值差距大于百分之0.5但小于百分之一，进行以下步骤。
            print(f"🟡 黄色预警：官方APR {lido_apr:.4f}% vs 链上APR {apr_onchain*100:.4f}%，差距 {apr_diff:.4f}%，需要关注。")
        else:#如果都不在上述区间内，指0.5到1这个区间内，就提醒我们情况正常
            print(f"✅ APR数据正常，官方与链上差距 {apr_diff:.4f}%，情况正常该吃吃该喝喝。")



    #下面的print模板是固定的，print(f"命名"(命名的附加说明)：{拿到的变量数据结果}")   后面的:,表示加千分位逗号     .2f表示保留两位小数     f表示按小数格式输出
    print("========== 最终结果 ==========")   
    print(f"ETH价格（Chainlink）: ${eth_price_chainlink}")
    print(f"ETH价格（Pyth）: ${eth_price_pyth}")
    print(f"stETH TVL（Chainlink）: ${steth_tvl_chainlink:,.2f}")
    print(f"stETH TVL（Pyth）: ${steth_tvl_pyth:,.2f}")
    print(f"其他代币TVL: ${other_tvl_第一种方法:,.2f}")
    print(f"总TVL（Chainlink）: ${total_tvl_CHAINLINK:,.2f}")
    print(f"总TVL（Pyth）: ${total_tvl_pyth:,.2f}")
    print(f"DefiLlama官方api总TVL: ${Defillama_tvl:,.2f}")



    #以下是第二阶段代码


    now=datetime.now(tz=shanghai_tz).strftime("%Y-%m-%d %H:%M:%S")#用now命名获取现在这个时间的变量，用datetime工具拿到的实时时间，拿到的数据我们要求转换为以年月日时分秒格式。
    hour = datetime.now(tz=shanghai_tz).hour#获取当前具体小时，后面进行每个小时数据记录和日环比分析时需要用到。
    weekday = datetime.now(tz=shanghai_tz).weekday()#获取当前具体是星期几，后面进行周报分析需要用到。

    record={#把本次运行的数据按固定格式把所需的变量组合打包形成一个字典，后续需要引用这个字典，字典用record命名。

        "timestamp": now,
        "eth_price_chainlink": eth_price_chainlink,
        "eth_price_pyth": eth_price_pyth,
        "steth_supply_eth": total_supply_eth,
        "steth_tvl_chainlink": steth_tvl_chainlink,
        "steth_tvl_pyth": steth_tvl_pyth,
        "other_tvl": other_tvl_第一种方法,
        "total_tvl_chainlink": total_tvl_CHAINLINK,
        "total_tvl_pyth": total_tvl_pyth,
        "Defillama_tvl": Defillama_tvl,
        "lido_apr": lido_apr,
        "apr_onchain": apr_onchain,
    }

    #下面是记录每小时实时数据数据的代码。先判断有没有已经存储了历史记录数据的文件，然后再根据有无文件的逻辑判断执行不同的写入数据的命令。
    filename = os.getenv("HISTORY_FILE")
    os.makedirs(os.path.dirname(filename), exist_ok=True)#确保/data目录存在，不存在就自动创建，防止首次运行时找不到目录报错。
    if os.path.exists(filename):#现在开始条件判断，通过os工具找对应路径里是否存在这个文件，如果已经存在了，那么就执行下面的with open命令打开这个文件。现在通过os工具直接去电脑硬盘找这个文件。
        with open(filename,"r",encoding="utf-8") as file:#那么就用r只读的形式，utf-8的编码方式去识别读取这个filename文件里面的数据，然后把都文件这个过程用file命名。现在找到这个文件了，现在用只读的方式读取这个硬盘里面的文件，然后把这个文件里面的数据搬到内存等待加工，把这个搬运的操作称为file。
            history=json.load(file)#现在用json翻译官去执行file里面内容读取翻译任务，因为python不能直接读取json格式文件的数据，需要用json在中间先充当翻译官先翻译，然后把经过json翻译过的，能够直接让python读取的这些数据命名为history变量。现在搬运到内存里面待加工的数据是json格式，python不能直接读取加工，需要用json工具把这些数据翻译成python可以自己读取的列表。
    else:#否则（指没有满足if上述条件判断，也就是要求对应的路径里没有这个文件，也意味着我们这个程序没运行过，这次是第一次运行。）
        history=[]#那么现在就定义一个空列表取名叫history，后面的运行数据都放到这个空列表里面。没有在硬盘里找到这个文件，就直接在内存里面创建一个空列表。

    history.append(record)#把本次运行形成的数据按照record字典要求的格式写入到history列表里面，append表示放到最后接上。如果已经有这个json文件的存在里面有历史数据，就把这次运行的数据加到被翻译过后的列表里面（现在还是在内存中操作）。如果没有历史数据存在，直接就在内存里这个空列表里写入这次运行的数据。

    with open(filename,"w",encoding="utf-8") as file:#用这个命令打开filename位置里的对应文件，命令这个文件是w可写入形式，用file命名这个要写入数据的状态，把改动以后的经过内存里加工后的history文件写进回硬盘里面。现在已经在内存里面加工好了这个列表，现在需要把加工好的列表写入到硬盘里面。
        json.dump(history,file,ensure_ascii=False,indent=2)#现在把上面已经加入了这次运行数据后的history列表用json翻译官翻译过的数据写回到json脚本里面去。ensure_ascii=False表示不使用ascii编码,直接使用中文形式，indent=2表示每个数据之间缩进两个空格，方便阅读。现在把已经加工好的列表用json工具翻译成可以写入到硬盘的json格式，然后写回到硬盘里面 。
    print(f"数据已经保存到{filename}文件里面，记录时间:{now}")#提示每个小时整点记录的数据已经保存到对应位置了。


    #以下是分析修改过的历史数据的过程，从lido_tvl_history.json文件里面读取包括本次运行以后写入的最新数据。
    with open(os.getenv("HISTORY_FILE"),"r",encoding="utf-8") as file:#打开路径里面存的这个脚本，以只读方式打开，这个状态称为file文件。到硬盘里面找到刚刚修改过更新过数据的这个文件，然后用只读的方式把里面的数据搬运到内存里。
        history1=json.load(file)#用json翻译官把file文件里读取的数据翻译上传给python使用,python读取到已经更新过的这个文件的过程定义为history1，为了和上面的没修改过数据的history变量区分。把搬运到内存里的数据用json工具把源json格式翻译成python可以直接读取的列表形式，然后等待内存里面加工待用，这里为了和上面区别，命名一个history1。
    latest=history1[-1]#用latest定义最新的一条数据，就是本次运行获取的数据，用于下面每小时打印当前实时数据时引用。现在内存里的经过翻译的列表，找到最新的一条数据，用latest命名。

    tg_hourly_msg = f"""
==============================
////Lido 小时数据记录////

时间：{latest["timestamp"]}

$Chainlink数据$
ETH价格：${latest["eth_price_chainlink"]:.2f}
总TVL：${latest["total_tvl_chainlink"]:,.2f}

$Pyth数据$
ETH价格：${latest["eth_price_pyth"]:.2f}
总TVL：${latest["total_tvl_pyth"]:,.2f}

$Defillama数据$
总TVL：${latest["Defillama_tvl"]:,.2f}
==============================
"""
    print(tg_hourly_msg)#打印反馈的每个小时的最新实时数据，用latest拿到本次运行的最新数据，时间，eth价格，总锁仓量，defillama总锁仓量。
    send_tg(tg_hourly_msg)#每小时把数据摘要推送到Telegram。

    if len(history1)<2:#这是防止程序崩溃报错的写法，有可能这是程序第一次运行，或者是以前的数据没有了，前面还没有记录，让程序不会因为找不到目标数据直接崩溃。
        print("历史数据不足，跳过小时预警分析")#给我们没有数据情况下运行的反馈
    else:#指的是有目标数据了，执行以下程序运行。
        previous=history1[-2]#取倒数第二条数据。
        latest=history1[-1]#取倒数第一条数据，也就是刚刚运行写入这条。
        tvl_hourly_change=latest["total_tvl_chainlink"]-previous["total_tvl_chainlink"]#取对应字段进行差距运算，定义为supply_hourly_change变量。
        tvl_hourly_change_percentage=tvl_hourly_change/previous["total_tvl_chainlink"]*100#算出每个小时与前一个小时的差距比例。
        print(f"TVL变化额：${tvl_hourly_change:,.2f}")#打印小时tvl具体变化数据。
        print(f"TVL变化幅度：{tvl_hourly_change_percentage:.2f}%")#打印每个小时变化幅度
        if tvl_hourly_change_percentage<-0.5:#如果变化幅度下降了百分之0.5就进行红色提醒
            print(f"链上总锁仓量在过去1小时内减少了{abs(tvl_hourly_change_percentage):.4f}%，🔴大户都在跑路了，快跑！")
        elif tvl_hourly_change_percentage<-0.1:#如果下降大于百分之0.1但是没到百分之0.5就进行黄色预警
            print(f"链上总锁仓量在过去1小时内减少了{abs(tvl_hourly_change_percentage):.4f}%，🟡可能存在风险，需要注意了。")
        else:#变化都不在这个区间里面，直接提醒数据正常
            print(f"链上总锁仓量在过去1小时内变化不大，✅数据正常，该吃吃该喝喝。")


    #以下创建以早晨八点为基准的日环比变化数据的变量备用，以change命名，方便后面gpt分析数据时引用。
    target_today_8am=datetime.now(tz=shanghai_tz).replace(hour=8,minute=0,second=0,microsecond=0,tzinfo=None)#我们现在需要定位一个理想时间点，我们规定为今天早上八点整，因为datetime.now()获取到的时间是年月日带时分秒的，但是实际上我们只想取今天的年月日，所以后面我们用八点整把现在拿到的时间替换了，目的是为了要今天日期的和八点整这两个时间点，因为不能写死了，所以后面用replace工具把现在拿到的时间替换成我们理想的时间点。这个今天的理想时间点用target_today_8am命名。
    today_real_8am=find_closest(history1, target_today_8am)#用find_closest替换min，在0.5小时范围内找今天8点附近的数据，找不到返回None。把对应参数放回定义的find_closest函数里进行使用，找到里锚定时间点不超过半小时的那条数据来使用，找不到就返回空集none。

    target_yesterday_8am=(datetime.now(tz=shanghai_tz)-timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0,tzinfo=None)#用datetime.now()获取到现在的日期时间，然后用timedelta往前推一天，然后把时间强制改为八点整，这个昨天的理想时间点用target_yesterday_8am命名。
    yesterday_real_8am=find_closest(history1, target_yesterday_8am)#用find_closest替换min，在0.5小时范围内找昨天8点附近的数据，找不到返回None。把对应参数放回定义的find_closest函数里进行使用找到里锚定时间点不超过半小时的那条数据来使用，找不到就返回空集none。

    if today_real_8am is None or yesterday_real_8am is None:#如果几天或者昨天的时间锚定点里面任中返回一个空集，就是说有数据找不到，那么就没办法进行日环比计算。
        print("⚠️ 历史数据不足，跳过日环比分析")#打印日环比分析失败提醒我们。
    else:#今天和昨天的数据都找到了，正常执行日环比分析。

        #chainlink数据的变化分析
        eth_change_chainlink_real_8am=today_real_8am["eth_price_chainlink"]-yesterday_real_8am["eth_price_chainlink"]#用eth_change_chainlink_am定义今天和昨天早上8点的eth价格差。
        eth_change_chainlink_percentage_real_8am=eth_change_chainlink_real_8am/yesterday_real_8am["eth_price_chainlink"]*100#用eth_change_chainlink_percentage_am定义今天和昨天早上8点的eth价格差占昨天eth价格变化的百分比。

        tvl_change_chainlink_real_8am=today_real_8am["total_tvl_chainlink"]-yesterday_real_8am["total_tvl_chainlink"]#用tvl_change_chainlink定义今天和昨天早上8点的总锁仓量差。
        tvl_change_chainlink_percentage_real_8am=tvl_change_chainlink_real_8am/yesterday_real_8am["total_tvl_chainlink"]*100#用tvl_change_chainlink_percentage_am定义今天和昨天早上8点的总锁仓量差占昨天总锁仓量变化的百分比。

        #pyth数据的变化分析
        eth_change_pyth_real_8am=today_real_8am["eth_price_pyth"]-yesterday_real_8am["eth_price_pyth"]#用eth_change_pyth_am定义今天和昨天早上8点的eth价格差。
        eth_change_pyth_percentage_real_8am=eth_change_pyth_real_8am/yesterday_real_8am["eth_price_pyth"]*100#用eth_change_pyth_percentage_am定义今天和昨天早上8点的eth价格差占昨天eth价格变化的百分比。

        tvl_change_pyth_real_8am=today_real_8am["total_tvl_pyth"]-yesterday_real_8am["total_tvl_pyth"]#用tvl_change_pyth_am定义今天和昨天早上8点的总锁仓量差。
        tvl_change_pyth_percentage_real_8am=tvl_change_pyth_real_8am/yesterday_real_8am["total_tvl_pyth"]*100#用tvl_change_pyth_percentage_am定义今天和昨天早上8点的总锁仓量差占昨天总锁仓量变化的百分比。

        #defillama数据的变化分析
        defillama_change_tvl_real_8am=today_real_8am["Defillama_tvl"]-yesterday_real_8am["Defillama_tvl"]#用defillama_change_tvl_am定义今天和昨天早上8点的总锁仓量差。
        defillama_change_tvl_percentage_real_8am=defillama_change_tvl_real_8am/yesterday_real_8am["Defillama_tvl"]*100#用defillama_change_tvl_percentage_8am定义今天和昨天早上8点的总锁仓量差占昨天总锁仓量变化的百分比。

        #以下是日环比tvl预警分析代码
        if tvl_change_chainlink_percentage_real_8am < -10:#一天内日环比下降了百分之十以上
            print(f"链上总锁仓量在过去1天内减少了{abs(tvl_change_chainlink_percentage_real_8am):.4f}%，🔴大户都在跑路了，快跑！")
        elif tvl_change_chainlink_percentage_real_8am < -5:#一天内日环比下降大于百分之五但不到百分之十
            print(f"链上总锁仓量在过去1天内减少了{abs(tvl_change_chainlink_percentage_real_8am):.4f}%，🟡可能存在风险，需要注意了。")
        else:#指不在两个区间里面，提醒正常
            print(f"链上总锁仓量在过去1天内变化不大，✅数据正常，该吃吃该喝喝。")

        #以下是日环比apr预警分析代码
        if today_real_8am.get("apr_onchain") is not None and yesterday_real_8am.get("apr_onchain") is not None:#指的如果是两个数据都同时拿到了，都没有返回空集，那么执行以下操作，我们这里用链上计算的apr数据为来源，以每天早晨8点为锚定时间戳。
            apr_onchain_today = today_real_8am.get("apr_onchain")#这次运行的8点的链上apr数据
            apr_onchain_yesterday = yesterday_real_8am.get("apr_onchain")#上一次运行的，前一天8点时候的apr数据
            apr_onchain_change_pct = (apr_onchain_today - apr_onchain_yesterday) / apr_onchain_yesterday * 100#算出两者的差距，进行官方给的和链上计算的差，然后进行差值运算。

            print(f"链上APR变化：{apr_onchain_yesterday*100:.4f}% -> {apr_onchain_today*100:.4f}%，日环比：{apr_onchain_change_pct:.2f}%")#打印出具体差值是多少，打印反馈给我们。

            if apr_onchain_change_pct < -20:#apr对比昨天下降百分之20的情况进行红色预警
                print(f"🔴 红色预警：链上APR日环比下降 {abs(apr_onchain_change_pct):.2f}%，收益率暴跌！")
            elif apr_onchain_change_pct < -10:#apr对比昨天下降百分之10的情况进行黄色预警
                print(f"🟡 黄色预警：链上APR日环比下降 {abs(apr_onchain_change_pct):.2f}%，需要关注。")
            elif apr_onchain_change_pct > 20:#apr对比昨天上涨百分之20的情况进行红色预警
                print(f"🔴 红色预警：链上APR日环比上涨 {apr_onchain_change_pct:.2f}%，异常暴涨疑似刷数据！")
            elif apr_onchain_change_pct > 10:#apr对比昨天上涨百分之10的情况进行黄色预警
                print(f"🟡 黄色预警：链上APR日环比上涨 {apr_onchain_change_pct:.2f}%，需要关注。")
            else:#都不在上诉区间内，提醒数据正常
                print(f"✅ 链上APR正常，日环比变化 {apr_onchain_change_pct:.2f}%，无需预警。")
        else:#指的是链上计算数据返回了空集，只要有一个返回空，整个apr变化都没办法计算 。
            print("APR历史数据不足，跳过日环比预警")#没办法计算我们也只能打印出无法计算反馈，不能让程序崩溃掉。

        #以下是AI分析日环比过程的代码
        if hour == 8:#如果现在的时间是早上八点整，那么就执行下面的代码。
            print("现在是早上八点，进行日环比分析")
            report_text = f"""
////Lido 日报 - 日环比分析////

参考时间昨天:{yesterday_real_8am["timestamp"]}                                                              
参考时间今天:{today_real_8am["timestamp"]}
$chainlink数据的分析$
ETH价格变化:${yesterday_real_8am["eth_price_chainlink"]:.2f} -> ${today_real_8am["eth_price_chainlink"]:.2f}
价差和百分百变化:{eth_change_chainlink_real_8am} //// ({eth_change_chainlink_percentage_real_8am:.2f}%)
总锁仓量变化:${yesterday_real_8am["total_tvl_chainlink"]:.2f} -> ${today_real_8am["total_tvl_chainlink"]:.2f}
价差和百分百变化:{tvl_change_chainlink_real_8am} //// ({tvl_change_chainlink_percentage_real_8am:.2f}%)

$pyth数据的分析$
ETH价格变化:${yesterday_real_8am["eth_price_pyth"]:.2f} -> ${today_real_8am["eth_price_pyth"]:.2f}
价差和百分百变化:{eth_change_pyth_real_8am} //// ({eth_change_pyth_percentage_real_8am:.2f}%)
总锁仓量变化:${yesterday_real_8am["total_tvl_pyth"]:.2f} -> ${today_real_8am["total_tvl_pyth"]:.2f}
价差和百分百变化:{tvl_change_pyth_real_8am} //// ({tvl_change_pyth_percentage_real_8am:.2f}%)

$defillama数据的分析$
总锁仓量变化:${yesterday_real_8am["Defillama_tvl"]:.2f} -> ${today_real_8am["Defillama_tvl"]:.2f}
价差和百分百变化:{defillama_change_tvl_real_8am} //// ({defillama_change_tvl_percentage_real_8am:.2f}%)
"""
            print(report_text)

            #日环比分析gpt的调用过程
            gpt_daily_result = call_gpt(messages=[
                    {"role": "system",
                    "content": "你是一个专业的DeFi数据分析师，擅长分析Lido协议的TVL和ETH价格走势。"},
                    {"role": "user",
                    "content": f"""{report_text}                                    
以下是Lido协议的日环比变化数据，请你分析这些数据，并给出结论：                                    
1. 分析ETH价格和tvl的变化情况
2. ETH价格的涨跌是否带动了TVL同向变化
3. 如果价格涨但TVL跌，或者价格跌但TVL涨，说明了什么
4. 给出资金流动的风险提示
5. 判断变化是正常波动还是异常信号
"""}
                ],
                model="gpt-5.5"
            )
            if gpt_daily_result is not None:
                print(gpt_daily_result)

            #以下是把通过gpt分析的日环比变化数据存到对应json文件的代码。
            daily_result_filename = os.getenv("DAILY_FILE")

            if os.path.exists(daily_result_filename):
                with open(daily_result_filename, "r", encoding="utf-8") as file:
                    daily_history = json.load(file)
            else:
                daily_history = []
            daily_history.append({
                "timestamp": today_real_8am["timestamp"],
                "report": report_text,
                "gpt_analysis": gpt_daily_result
            })

            with open(daily_result_filename, "w", encoding="utf-8") as file:
                json.dump(daily_history, file, ensure_ascii=False, indent=2)

            print(f"日环比分析已保存到{daily_result_filename}")

    #下面是gpt分析的周报过程
    if hour == 8 and weekday == 6:#如果当前时间正好是早上八点，并且今天是周天，那么就执行下面命令。
        with open(os.getenv("DAILY_FILE"), "r", encoding="utf-8") as file:#用只读命令把日报记录文件里面的数据搬到内存里面等待处理。
            daily_history = json.load(file)#在内存里用json翻译官翻译日报里的数据给python读取使用。
        
        week_daily = daily_history[-7:]#用week_daily定义过去七天的每日每条数据，是包含七条数据的一个列表。

        week_report_text = ""#定义一个空字符串，方便后面累加周报内容。
        for day in week_daily:#把week_daily列表里面的每条数据一条一条拆开，每条数据取名为day。
            week_report_text += f"\n{day['report']}\n"#把取的每条数据day里面的report字段对应的数据取出来一条一条的放进week_report_text这个列表里面，可以避免其他杂乱字段的干扰。

    #周报分析gpt的调用过程
        gpt_week_result = call_gpt(messages=[#这是把我们要发给gpt的提示词装进message字典，字典里包括了具体数据week_report_text，还有文字提问。最后把字典一起打包发给gpt回答，这样直接引用前面我们定义的call_gpt函数，而不用重复填写重复的基本参数，节省了很多工作量。
                {"role": "system",
                "content": "你是一个专业的DeFi数据分析师，擅长分析Lido协议的TVL和ETH价格走势。"},
                {"role": "user",
                "content": f"""{week_report_text}
以上是Lido协议过去七天的每日数据，请你：
1. 分析这一周ETH价格的整体走势
2. 分析这一周TVL的整体走势
3. 判断资金是整体流入还是流出Lido
4. 判断用户整体是在质押还是赎回stETH
5. 给出本周市场情绪的综合判断
6. 给出下周需要关注的风险点
"""}
            ],
            model="gpt-5.5"
        )#这几个括号就表示又内到外把函数公式一一对应运行关闭，和excel里的嵌套函数是一个原理。
        if gpt_week_result is not None:#意思是说如果gpt_week_result这个结果不是空集，就是说只要不是api没连上，或者连上了没返回回答的情况下，就执行以下步骤。
            print(gpt_week_result)#打印出gpt返回的有内容的回答。

    #下面是把gpt分析的周报存入对应json文本的过程
        week_result_filename = os.getenv("WEEK_FILE")

        if os.path.exists(week_result_filename):#这里开始条件判断，如果程序已经运行过，里面有历史数据了，就执行下面步骤。
            with open(week_result_filename, "r", encoding="utf-8") as file:#用只读方式把硬盘里这个文件里存储的数据放到内存里等待加工。
                week_history = json.load(file)#在内存里用json翻译官把数据翻译成python可读的形式待用。
        else:#指没有找到这个对应文件，可能是第一次运行。
            week_history = []#直接在内存里创建一个空列表待用。

        week_history.append({#在内存里把本次运行的新数据按以下格式加到到翻译过的原数据的后面。还是像上面一样分两种情况。
            "timestamp": today_real_8am["timestamp"],
            "week_report": week_report_text,
            "gpt_analysis": gpt_week_result
        })

        with open(week_result_filename, "w", encoding="utf-8") as file:#用可写方式打开硬盘里面储存的文件。
            json.dump(week_history, file, ensure_ascii=False, indent=2)#现在把内存里加工过的文件用json翻译官翻译回json格式写回到硬盘中去。

        print(f"周报分析已保存到{week_result_filename}")#提示我们周报已经成功保存到对应位置了。 

    #以下以周数据为例进行不同引导词的对比测试
        prompts={#创建字典，把引导词名称和具体引导内容打包成一个字典，方便后面引用。
"严格数据派" : f"""{week_report_text}
以下是Lido协议本周数据，请你：
1. 只基于数据说话，不要主观猜测
2. 找出本周最异常的一天，说明原因
3. 用一句话总结本周最重要的信号
""",
        "风险预警派" : f"""{week_report_text}
以下是Lido协议本周数据，请你扮演一个风控经理：
1. 找出所有潜在的风险信号
2. 判断资金是否在大规模流出
3. TVL下降是否已经达到警戒线
4. 给出1-10分的风险评级，并说明理由
5. 如果你是大户，看到这些数据你会怎么操作
"""
}
        for name,prompt_content in prompts.items():#prompts.items()是把上面我们定义的prompts字典拆开，拆开成为引导词名称（key）对应name变量，引导词内容（value）对应prompt_content变量，这里学了新知识，in后面是两个变量for后面也可以接两个变量，分别对应key和value。
            print(f"\n{'='*30}")#\n表示换行，'='*30表示30个等号，方便后面打印出来分割线。
            print(f"【{name}】的分析结果")#打印出来引导词名称
            print(f"{'='*30}")#打印出来分割线
        
            gpt_result = call_gpt(messages=[#这是把我们要发给gpt的提示词装进message字典，字典里包括了具体数据prompt_content，还有文字提问。最后把字典一起打包发给gpt回答，这样直接引用前面我们定义的call_gpt函数，而不用重复填写重复的基本参数，节省了很多工作量。
                    {"role": "system",
                    "content": "你是一个专业的DeFi数据分析师，擅长分析Lido协议的TVL和ETH价格走势。"},
                    {"role": "user",
                    "content": prompt_content}#这里prompt_content是可以变的变量，区别上面我们定死了引导内容，这里是根据不同的引导词名称，调用不同的引导内容。加了prompt前缀是为了和上面messages字典里的"content"键名区分，避免阅读时混淆。
                ],
                model="gpt-5.5"
            )
            if gpt_result is not None:#意思是说如果gpt_result这个结果不是空集，就是说只要不是api没连上，或者连上了没返回回答的情况下，就执行以下步骤。
                print(gpt_result)#打印出gpt返回的有内容的回答。


#定时调度：每小时整点执行一次job函数。
schedule.every().hour.at(":00").do(job)

job()#程序启动时立刻先运行一次，不用等到下一个整点。

while True:#程序一直保持运行状态，每60秒检查一次有没有到达执行时间。
    schedule.run_pending()
    time.sleep(60)
