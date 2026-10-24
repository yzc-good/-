# -*- coding: utf-8 -*-
"""Build self-contained HTML tool embedding bilingual + dictionary data."""
import json, os, glob, re

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, 'data', 'bilingual.json'), encoding='utf-8') as f:
    bil = json.load(f)

dic = {}

# 1) 大词库：data/exam_*.txt（格式 word~pos~释义）
for path in sorted(glob.glob(os.path.join(BASE, 'data', 'exam_*.txt'))):
    with open(path, encoding='utf-8-sig') as f:
        for raw in f:
            line = raw.strip().lstrip('\ufeff')
            if not line or line.startswith('#'):
                continue
            parts = line.split('~')
            if len(parts) < 3:
                continue
            w = parts[0].strip().lstrip('\ufeff')
            pos = parts[1].strip()
            zh = '~'.join(parts[2:]).strip()
            if not w or not zh:
                continue
            if not re.match(r"^[A-Za-z][A-Za-z'\- ]*$", w):
                continue
            dic[w.lower()] = {
                'headword': w,
                'ipa': '',
                'pos': [p.strip() for p in pos.replace(',', '/').split('/') if p.strip()],
                'meanings': [{'zh': zh, 'en': ''}],
                'example': '',
            }

# 2) 精编词条（会覆盖上面的简版，信息更全）
for name in ['dictionary.json', 'dictionary_extra.json', 'dictionary_names.json']:
    p = os.path.join(BASE, 'data', name)
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            dic.update(json.load(f))

# 3) 一词多义扩充（dict_multi.json，来自有道）；合并进已有词条。
#    保留原词条的 example/syn/ant/notes，但用更全的多词性释义覆盖 pos/meanings/ipa。
_multi_path = os.path.join(BASE, 'data', 'dict_multi.json')
if os.path.exists(_multi_path):
    with open(_multi_path, encoding='utf-8') as f:
        multi = json.load(f)
    for key, mv in multi.items():
        if not key or not mv or not mv.get('meanings'):
            continue
        old = dic.get(key)
        merged = dict(old or {})
        merged['headword'] = mv.get('headword', old.get('headword', key) if old else key)
        merged['ipa'] = mv.get('ipa') or (old or {}).get('ipa', '')
        merged['pos'] = mv.get('pos') or []
        merged['meanings'] = [
            {'zh': s.get('zh', ''), 'en': s.get('en', ''),
             'pos': (s.get('pos') or '').replace('.', '').strip().lower()}
            for s in mv.get('meanings', []) if s.get('zh')
        ]
        # 保留原词条的 example/syn/ant/notes（合并保存）
        dic[key] = merged

# strip hidden markers
dic = {k: v for k, v in dic.items() if not v.get('hidden')}

# Build index by headword
index_word = {}
for key, val in dic.items():
    hw = val.get('headword', key)
    index_word[str(hw).lower()] = val

# --- Common function words & pronouns & basic words ---
func_words = {
 'the':'冠词 the（定冠词）','a':'冠词 a（不定冠词）','an':'冠词 an（不定冠词，用于元音前）',
 'to':'介词 to 往，向/不定式标记','in':'介词 in 在…之内','on':'介词 on 在…上面',
 'of':'介词 of …的','for':'介词 for 为了；持续','with':'介词 with 和…一起；具有',
 'and':'连词 and 和；并且','but':'连词 but 但是','or':'连词 or 或者',
 'is':'be 动词，单数（是）','are':'be 动词，复数（是）','was':'be 的过去式（是）',
 'were':'be 的过去式，复数（是）','be':'动词 be（是；存在）','been':'动词 be 的过去分词（曾经/已经）',
 'have':'动词 have 有；已经','has':'动词 have 的第三人称单数','had':'动词 have 的过去式/过去分词',
 'it':'代词 it 它','its':'代词 its 它的','they':'代词 they 他们；它们',
 'them':'代词 them 他们（宾格）','their':'代词 their 他们的','theirs':'代词 theirs 他（她）们的（所有物）',
 'this':'代词 this 这个','that':'代词 that 那个；引导从句','these':'代词 these 这些','those':'代词 those 那些',
 'at':'介词 at 在（某时/某地）；以','by':'介词 by 通过；在…旁边','as':'连词/介词 as 作为；当',
 'from':'介词 from 从…','who':'代词 who 谁；…的人','whose':'代词 whose 谁的',
 'whom':'代词 whom 谁（宾格）','when':'连词 when 当…时','what':'代词 what 什么',
 'there':'副词 there 那里；（there be）有','here':'副词 here 这里','where':'连词 where 哪里',
 'not':'副词 not 不；没有',"n't":'否定缩写 not','no':'副词/形容词 no 不；没有',
 'yes':'副词 yes 是；对','do':'动词 do 做；构成疑问/否定','does':'动词 do 的第三人称单数',
 'did':'动词 do 的过去式','so':'副词 so 如此；所以','such':'形容词 such 这样的',
 'just':'副词 just 刚刚；仅仅','only':'副词 only 只；仅仅','also':'副词 also 也',
 'very':'副词 very 很；非常','much':'副词 much 很多；非常','more':'副词 more 更多','most':'副词 most 最；最多',
 'many':'形容词 many 许多','some':'形容词 some 一些','all':'代词 all 所有；全部',
 'both':'代词 both 两者都','each':'代词 each 每个','every':'形容词 every 每一个',
 'few':'形容词 few 很少','several':'形容词 several 几个',
 'one':'数词 one 一；一个','two':'数词 two 二','three':'数词 three 三',
 'again':'副词 again 再次','once':'副词 once 一次；曾经','still':'副词 still 仍然',
 'already':'副词 already 已经','even':'副词 even 甚至','during':'介词 during 在…期间',
 'before':'介词 before 在…之前','after':'介词 after 在…之后','between':'介词 between 在…之间',
 'under':'介词 under 在…下面','over':'介词 over 在…上方；超过','about':'介词 about 关于；大约',
 'around':'介词 around 在…周围','away':'副词 away 离开','off':'副词 off 离开；关掉',
 'out':'副词 out 出去；在外面','into':'介词 into 进入…里面','onto':'介词 onto 到…上面',
 'if':'连词 if 如果','because':'连词 because 因为','though':'连词 though 虽然',
 'while':'连词 while 当…的时候；然而','until':'介词 until 直到','since':'介词 since 自从；因为',
 'than':'介词 than 比','whether':'连词 whether 是否','nor':'连词 nor 也不','neither':'代词 neither 两者都不',
 'too':'副词 too 也；太','also':'副词 also 也','could':'情态动词 could 能；可以','would':'情态动词 would 将；会',
 'should':'情态动词 should 应该','may':'情态动词 may 可以；也许','might':'情态动词 might 也许','must':'情态动词 must 必须',
 'will':'情态动词 will 将；愿意','can':'情态动词 can 能','shall':'情态动词 shall 将；shall 用于第一人称',
 'i':'代词 I 我','me':'代词 me 我（宾格）','my':'代词 my 我的','mine':'代词 mine 我的（所有物）',
 'you':'代词 you 你；你们','your':'代词 your 你的；你们的','yours':'代词 yours 你的（所有物）',
 'he':'代词 he 他','him':'代词 him 他（宾格）','his':'代词 his 他的',
 'she':'代词 she 她','her':'代词 her 她（宾格）；她的','hers':'代词 hers 她的（所有物）',
 'we':'代词 we 我们','us':'代词 us 我们（宾格）','our':'代词 our 我们的','ours':'代词 ours 我们的（所有物）',
 'no':'副词 no 不','said':'动词 say 的过去式（说）','he':'代词 he 他',
 'say':'动词 say 说','tell':'动词 tell 告诉','make':'动词 make 做；使','made':'动词 make 的过去式',
 'end':'动词 end 结束；终结','plan':'名词 plan 计划','people':'名词 people 人们',
 'show':'动词 show 显示；表明','show2':'名词 show 节目',
 'man':'名词 man 男人；人类','m':'名词 m（million）百万','million':'数词 million 百万',
 'the':'冠词 the','a':'冠词 a','an':'冠词 an',
 'according':'介词 according to 根据；按照','almost':'副词 almost 几乎；差不多',
 'being':'动词 be 的现在分词（being）；存在','build':'动词 build 建造；建设',
 'deep':'形容词 deep 深的；深刻的','focus':'动词/名词 focus 关注；焦点',
 'however':'副词 however 然而；不过','least':'副词 least 最少；（at least）至少',
 'nearly':'副词 nearly 几乎；将近','other':'形容词 other 其他的；其余的',
 'overwhelming':'形容词 overwhelming 压倒性的','prime':'名词 prime 首要的；首相（prime minister 首相/总理）',
 'quarter':'名词 quarter 四分之一；季度','radio':'名词 radio 广播；电台',
 'rather':'副词 rather 相当；（rather than 而不是）','someone':'代词 someone 某人',
 'take':'动词 take 拿起；采取；（take care of 照料）','think':'动词 think 想；认为',
 'times':'名词 time 的复数 times 次；时代；（at times 有时）','within':'介词 within 在…之内',
 'host':'名词 host 主持人；主人','going':'动词 go 的现在分词 going 去；将（be going to 将要）',
 'province':'名词 province 省；省份','provincial':'形容词 provincial 省的',
 'david':'人名 David 戴维','keith':'人名 Keith 基思','mark':'人名 Mark 马克',
 'guardian':'名词 Guardian《卫报》（英国报纸）','wilson':'人名 Wilson 威尔逊',
 'carney':'人名 Carney 卡尼','mark carney':'人名 Mark Carney 马克·卡尼（加拿大总理）',
 'don':"don't 的缩写（do not）", "don't":"缩写 do not（不，不作）",
}

inflect = {}
def add_inflection(word, base):
    inflect[word.lower()] = base.lower()

# Generate inflections from dictionary headwords
for key, val in dic.items():
    hw = str(val.get('headword', key)).lower()
    if not hw or hw == '—':
        continue
    add_inflection(hw + 's', hw)
    add_inflection(hw + 'es', hw)
    add_inflection(hw + 'ing', hw)
    add_inflection(hw + 'ed', hw)
    if hw.endswith('e'):
        add_inflection(hw + 'd', hw)
        add_inflection(hw[:-1] + 'ing', hw)
    if hw.endswith('y'):
        add_inflection(hw[:-1] + 'ies', hw)
        add_inflection(hw[:-1] + 'ied', hw)
    add_inflection(hw + 'er', hw)
    add_inflection(hw + 'est', hw)

# Document-specific irregular & phrasal inflections -> base in dictionary
doc_inflections = {
    'voters':'voter','votes':'vote','voted':'vote','counting':'count',
    'rejected':'reject','rejecting':'reject','rejection':'reject',
    'deepened':'deepen','deepening':'deepen',
    'accelerated':'accelerate','accelerating':'accelerate',
    'diversified':'diversify','diversifying':'diversify',
    'infrastructures':'infrastructure','separatists':'separatist',
    'supporters':'supporter','supported':'support','supporting':'support',
    'divisions':'division','chose':'choose','choosing':'choose',
    'chosen':'choose','grew':'grow','beginning':'begin','began':'begin',
    'backed':'back','made':'make','making':'make','said':'say','told':'tell',
    'felt':'feel','feels':'feel','spent':'spend','spending':'spend',
    'posted':'post','showed':'show','shown':'show','saw':'see','seen':'see',
    'voters':'voter','wanted':'want','wanting':'want','allowed':'allow',
    'allowing':'allow','better':'good','changed':'change','changes':'change',
    'moved':'move','moving':'move','results':'result','votes':'vote',
    'projects':'project','efforts':'effort','numbers':'number','threats':'threat',
    'grievances':'grievance','canadians':'canadian','albertans':'albertan',
    'residents':'resident','counting':'count','counted':'count',
    'celebrated':'celebrate','taxpayers':'taxpayer','peoples':'people',
    'things':'thing','waste':'waste','wasted':'waste','treat':'treat',
    'treated':'treat','needs':'need','needed':'need','sadnesses':'sadness',
    'moneys':'money','federals':'federal','divided':'division',
    'delivering':'deliver','delivered':'deliver','developing':'develop',
    'developed':'develop','leaving':'leave','leaves':'leave','left':'leave',
    'showed':'show',
}
for w, b in doc_inflections.items():
    if b:
        inflect[w.lower()] = b.lower()

# Add a few extra headwords referenced by inflections
if 'albertan' not in index_word:
    index_word['albertan'] = {"headword":"Albertan","ipa":"/ælˈbɜːrtən/","pos":["noun","adjective"],
        "meanings":[{"zh":"阿尔伯塔人；阿尔伯塔（人）的","en":"a person from Alberta, Canada"}],
        "example":"Most Albertans feel grievances. 多数阿尔伯塔人感到不满。"}
if 'resident' not in index_word:
    index_word['resident'] = {"headword":"resident","ipa":"/ˈrezɪdənt/","pos":["noun"],
        "meanings":[{"zh":"居民；住户","en":"a person who lives in a place"}],
        "example":"Residents felt the referendum was a distraction. 居民觉得公投是一种干扰。"}
if 'post' not in index_word:
    index_word['post'] = {"headword":"post","ipa":"/poʊst/","pos":["verb","noun"],
        "meanings":[{"zh":"发布；（网络）帖子；邮寄","en":"to publish online; to send by mail"}],
        "example":"A radio show host posted online. 一位电台主持人在网上发文。"}
if 'feel' not in index_word:
    index_word['feel'] = {"headword":"feel","ipa":"/fiːl/","pos":["verb"],
        "meanings":[{"zh":"感觉；感到","en":"to experience an emotion or sensation"}],
        "example":"Albertans feel deep grievances. 阿尔伯塔人深感不满。"}
if 'need' not in index_word:
    index_word['need'] = {"headword":"need","ipa":"/niːd/","pos":["verb","noun"],
        "meanings":[{"zh":"需要","en":"to require"}],
        "example":"Alberta needs to be treated better. 阿尔伯塔应该得到更好的对待。"}
if 'good' not in index_word:
    index_word['good'] = {"headword":"good","ipa":"/ɡʊd/","pos":["adjective"],
        "meanings":[{"zh":"好的；不错的","en":"of high quality; favourable"}],
        "example":"Better — 更好的（比较级）。"}
if 'change' not in index_word:
    index_word['change'] = {"headword":"change","ipa":"/tʃeɪndʒ/","pos":["verb","noun"],
        "meanings":[{"zh":"改变；变化","en":"to make or become different"}],
        "example":"Most Albertans want some thing changed. 多数阿尔伯塔人都希望有些改变。"}
if 'develop' not in index_word:
    index_word['develop'] = {"headword":"develop","ipa":"/dɪˈveləp/","pos":["verb"],
        "meanings":[{"zh":"发展；开发","en":"to grow or build"}],
        "example":"Develop major infrastructure projects. 开发重大基础设施项目。"}
if 'supporter' not in index_word:
    index_word['supporter'] = {"headword":"supporter","ipa":"/səˈpɔːrtər/","pos":["noun"],
        "meanings":[{"zh":"支持者；拥护者","en":"a person who supports someone or something"}],
        "example":"Supporters of Canadian unity. 加拿大统一的支持者。"}

def build_payload():
    return {
        'bilingual': bil,
        'dictionary': index_word,
        'inflect': inflect,
        'funcWords': func_words,
    }


def main():
    payload = build_payload()
    with open(os.path.join(BASE, 'template.html'), encoding='utf-8') as f:
        html = f.read()
    html = html.replace('/*__DATA__*/', 'window.APP_DATA = ' + json.dumps(payload, ensure_ascii=False) + ';')
    out = os.path.join(BASE, 'EnglishTranslator.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, os.path.getsize(out), 'bytes')
    print('dict words:', len(index_word), '| inflections:', len(inflect))


if __name__ == '__main__':
    main()