from ml import *
from collections import OrderedDict
import re

USELESS_CHARS = re.compile(r'ÿc[\d;:]|●|★|◆|\}', re.DOTALL)

def log(*args, **kwargs):
    # print(*args, **kwargs)
    pass

def loadTableFile(filename: str) -> list[bytes]:
    return open(filename, 'rb').read().splitlines()

def printList(data: list[str], headers: list[str] = []):
    if not headers:
        headers = [''] * len(data)

    else:
        assert len(data) == len(headers)

    for i in range(len(data)):
        log(f'[{i}] {headers[i]}: `{data[i]}`')

def minmax(min, max, *, sign = False, parentheses = True) -> str:
    if max is None:
        value = f'{min}'

    elif min == max:
        value = f'{min}'

    else:
        value = f'({min}-{max})'
        if not parentheses:
            value = value.strip('()')

    if sign and min > 0:
        value = '+' + value

    return value

def toInt(s: str, defval = None) -> int | None:
    return int(s) if s else defval

class TableData:
    @staticmethod
    def parse(line: str) -> list[str]:
        return line.split('\t')

    def __repr__(self) -> str:
        return self.__str__()

class StringTableData(TableData):
    def __init__(self, line: str):
        self.key, self.value = self.parse(line)

    def __str__(self) -> str:
        return f'{self.key}: {self.value}'

class StringTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.data       = OrderedDict()     # type: dict[str, StringTableData]
        self.dataList   = []                # type: list[StringTableData]
        self.keyIndex   = {}                # type: dict[str | int, str | int]

        for l in lines:
            if not l:
                continue

            l = l.decode('UTF8')

            data = StringTableData(l)
            self.dataList.append(data)

            if data.key == 'x':
                continue

            try:
                data = self.data.pop(data.key)
            except KeyError:
                pass

            self.data[data.key] = data

        self.buildKeyIndex()

    def buildKeyIndex(self):
        self.keyIndex.clear()
        for index, key in enumerate(self.data.keys()):
            self.keyIndex[index] = key
            self.keyIndex[key] = index

    def update(self, tbl: 'StringTable'):
        for k, v in tbl.data.items():
            try:
                del self.data[k]
            except KeyError:
                pass

            self.data[k] = v

        self.buildKeyIndex()
        return self

    def strip(self, s: str) -> str:
        for p in USELESS_CHARS.findall(s):
            s = s.replace(p, '')

        return s.strip()

    def get(self, key: str) -> str:
        return self.strip(self.data[key].value)

    def getIndex(self, index: int) -> str:
        return self.strip(self.dataList[index].value)

    def getOffset(self, key: str, offset: int) -> str:
        i = self.keyIndex[key]
        return self.get(self.keyIndex[i + offset])

    def getSkillName(self, skillId: int) -> str:
        key = f'skillname{skillId}'
        value = self.data.get(key)
        if value is not None:
            return self.strip(value.value)

        key = f'Skillname{skillId}'
        value = self.data.get(key)
        if value is not None:
            return self.strip(value.value)

        return f'<missing skillname>{skillId}'

    def getSkillTab(self, skillTabId: int) -> str:
        # https://d2mods.info/forum/kb/viewarticle?a=45

        return self.get([
            'StrSklTabItem3',   # 0 - 弓和十字弓技能
            'StrSklTabItem2',   # 1 - 被动和魔法技能
            'StrSklTabItem1',   # 2 - 镖枪和长矛技能

            'StrSklTabItem15',  # 3 - 火焰系技能
            'StrSklTabItem14',  # 4 - 闪电系技能
            'StrSklTabItem13',  # 5 - 冰冷系技能

            'StrSklTabItem8',   # 6 - 诅咒
            'StrSklTabItem7',   # 7 - 毒素和白骨技能
            'StrSklTabItem9',   # 8 - 召唤技能

            'StrSklTabItem6',   # 9 - 战斗技能
            'StrSklTabItem5',   # 10 - 攻击性灵气
            'StrSklTabItem4',   # 11 - 防御性灵气

            'StrSklTabItem10',  # 12 - 战嚎
            'StrSklTabItem12',  # 13 - 支配性
            'StrSklTabItem11',  # 14 - 战斗技能

            'StrSklTabItem16',  # 15 - 召唤系技能
            'StrSklTabItem17',  # 16 - 变形系技能
            'StrSklTabItem18',  # 17 - 元素系技能

            'StrSklTabItem19',  # 18 - 陷阱
            'StrSklTabItem20',  # 19 - 影子训练
            'StrSklTabItem21',  # 20 - 武学艺术
        ][skillTabId])

    def getClassOnly(self, classId: int) -> str:
        return self.get([
            'AmaOnly',
            'SorOnly',
            'NecOnly',
            'PalOnly',
            'BarOnly',
            'DruOnly',
            'AssOnly',
        ][classId])

class WeaponsTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.name           = items[0]
        self.type           = items[1]
        self.code           = items[3]
        self.namestr        = items[5]
        self.reqstr         = toInt(items[23])
        self.reqdex         = toInt(items[24])
        self.durability     = toInt(items[25])

    def __str__(self) -> str:
        return '\n'.join([
            f'index     = {self.index}',
            f'name      = {self.name}',
            f'type      = {self.type}',
            f'code      = {self.code}',
            f'namestr   = {self.namestr}',
            f'reqstr    = {self.reqstr}',
            f'reqdex    = {self.reqdex}',
            f'durability= {self.durability}',
        ])

class WeaponsTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, WeaponsTableData]

        index = 1

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)

            data = WeaponsTableData(index, l)
            if data.name == 'Expansion':
                continue

            index += 1

            if data.code in self.data:
                raise NotImplementedError(f'dup: ${data.code}')

            self.data[data.code] = data
            if data.name.strip() != data.code:
                log(data)
                raise

    def get(self, code: str) -> WeaponsTableData | None:
        return self.data.get(code)

    def getWeaponDesc(self, item: WeaponsTableData) -> str | None:
        return {
            'staf'  : 'WeaponDescStaff',
            'axe'   : 'WeaponDescAxe',
            'swor'  : 'WeaponDescSword',
            'knif'  : 'WeaponDescDagger',
            'spea'  : 'WeaponDescSpear',
            'pole'  : 'WeaponDescPoleArm',
            'bow'   : 'WeaponDescBow',
            'xbow'  : 'WeaponDescCrossBow',
            'tpot'  : 'WeaponDescThrowPotion',
            'jave'  : 'WeaponDescJavelin',
            'blun'  : 'WeaponDescMace',
            'h2h'   : 'WeaponDescH2H',
            'h2h2'  : 'WeaponDescH2H',
        }.get(item.type)

class ArmorTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.name           = items[0]
        self.reqstr         = toInt(items[9])
        self.reqdex         = toInt(items[10])
        self.durability     = toInt(items[12])
        self.levelreq       = items[15]
        self.code           = items[18]
        self.namestr        = items[19]

    def __str__(self) -> str:
        return '\n'.join([
            f'index         = {self.index}',
            f'name          = {self.name}',
            f'reqstr        = {self.reqstr}',
            f'reqdex        = {self.reqdex}',
            f'durability    = {self.durability}',
            f'levelreq      = {self.levelreq}',
            f'code          = {self.code}',
            f'namestr       = {self.namestr}',
        ])

class ArmorTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, ArmorTableData]

        index = 1001

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)

            data = ArmorTableData(index, l)
            if data.name == 'Expansion':
                continue

            index += 1

            if data.code in self.data:
                raise NotImplementedError(f'dup: ${data.code}')

            self.data[data.code] = data
            if data.name.strip() != data.code:
                log(data)
                raise

    def get(self, code: str) -> ArmorTableData | None:
        return self.data.get(code)

class MiscTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.name           = items[0]
        self.levelreq       = items[6]
        self.code           = items[13]
        self.namestr        = items[15]

    def __str__(self) -> str:
        return '\n'.join([
            f'index     = {self.index}',
            f'name      = {self.name}',
            f'levelreq  = {self.levelreq}',
            f'code      = {self.code}',
            f'namestr   = {self.namestr}',
        ])

class MiscTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, MiscTableData]

        index = 2001

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)

            data = MiscTableData(index, l)
            if data.name == 'Expansion':
                continue

            index += 1

            if data.code in self.data:
                raise NotImplementedError(f'dup: ${data.code}')

            self.data[data.code] = data

    def get(self, code: str) -> MiscTableData | None:
        return self.data.get(code)

class GemsTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.name           = items[0]
        self.code           = items[3]
        self.levelreq       = 0
        self.weaponProps    = [Property(*p) for p in zip(*[iter(items[5:17])]*4) if p[0]]
        self.helmProps      = [Property(*p) for p in zip(*[iter(items[17:29])]*4) if p[0]]
        self.shieldProps    = [Property(*p) for p in zip(*[iter(items[29:41])]*4) if p[0]]

    def __str__(self) -> str:
        return '\n'.join([
            f'index         = {self.index}',
            f'name          = {self.name}',
            f'code          = {self.code}',
            f'levelreq      = {self.levelreq}',
            f'weaponProps   = {self.weaponProps}',
            f'helmProps     = {self.helmProps}',
            f'shieldProps   = {self.shieldProps}',
        ])

class GemsTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, GemsTableData]

        index = 1

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)
            # raise

            data = GemsTableData(index, l)
            if data.name == 'Expansion':
                continue

            index += 1

            if data.code in self.data:
                raise NotImplementedError(f'dup: ${data.code}')

            self.data[data.code] = data

    def get(self, code: str) -> GemsTableData | None:
        return self.data[code]

class SkillTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.skill          = items[0]
        self.id             = toInt(items[1], 0)
        self.charclass      = toInt(items[2], 0)
        self.skilldesc      = toInt(items[3], 0)

    def __str__(self) -> str:
        return '\n'.join([
            f'index     = {self.index}',
            f'skill     = {self.skill}',
            f'id        = {self.id}',
            f'charclass = {self.charclass}',
            f'skilldesc = {self.skilldesc}',
        ])

class SkillTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers    = TableData.parse(lines[0].decode('UTF8'))
        self.data       = {}    # type: dict[int, SkillTableData]
        self.dataByName = {}    # type: dict[str, SkillTableData]

        index = 0

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')

            data = SkillTableData(index, l)
            index += 1

            if data.id in self.data:
                raise NotImplementedError(f'dup: ${data.id}')

            self.data[data.id] = data
            self.dataByName[data.skill] = data

    def get(self, id: int) -> SkillTableData:
        if isinstance(id, int):
            return self.data[id]

        return self.getByName(id)

    def getByName(self, name: str) -> SkillTableData:
        return self.dataByName[name]

class SkillDescTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index      = index
        self.skilldesc  = items[0]
        self.strname    = toInt(items[7])
        self.strshort   = toInt(items[8])
        self.strlong    = toInt(items[9])
        self.stralt     = toInt(items[10])
        self.strmana    = toInt(items[11])

    def __str__(self) -> str:
        return '\n'.join([
            f'index     = {self.index}',
            f'skilldesc = {self.skilldesc}',
            f'strname   = {self.strname}',
            f'strshort  = {self.strshort}',
            f'strlong   = {self.strlong}',
            f'stralt    = {self.stralt}',
            f'strmana   = {self.strmana}',
        ])

class SkillDescTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = []  # type: list[SkillDescTableData]

        index = 0

        for index, l in enumerate(lines[1:]):
            if not l:
                continue

            l = l.decode('cp1252')

            data = SkillDescTableData(index, l)
            self.data.append(data)

    def get(self, code: str) -> SkillDescTableData:
        return self.data[code]

class CharStatTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index      = index
        self.charclass  = items[0]      # `Amazon`
        self.allSkills  = items[43]     # `ModStr3a`
        self.skillTabs  = [
            items[44],     # `StrSklTabItem3`
            items[45],     # `StrSklTabItem2`
            items[46],     # `StrSklTabItem1`
        ]
        self.classOnly  = items[47]     # `AmaOnly`

    def __str__(self) -> str:
        return '\n'.join([
            f'index     = {self.index}',
            f'charclass = {self.charclass}',
            f'allSkills = {self.allSkills}',
            f'skillTabs = {self.skillTabs}',
            f'classOnly = {self.classOnly}',
        ])

class CharStatTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = []  # type: list[CharStatTableData]

        index = 0
        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)
            # raise

            data = CharStatTableData(index, l)
            if data.charclass == 'Expansion':
                continue

            index += 1
            self.data.append(data)

    def get(self, charclass: int) -> CharStatTableData:
        return self.data[charclass]

class PropertyTableData(TableData):
    class Function(TableData):
        def __init__(self, index: int, set: str, val: str, func: str, stat: str):
            self.index  = index
            self.set    = toInt(set)
            self.val    = toInt(val)
            self.func   = toInt(func)
            self.stat   = stat

        def __str__(self) -> str:
            return '\n'.join([
                f'index = {self.index}',
                f'set   = {self.set}',
                f'val   = {self.val}',
                f'func  = {self.func}',
                f'stat  = {self.stat}',
            ])

    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index  = index
        self.code   = items[0]
        self.funcs  = [PropertyTableData.Function(index, *p) for index, p in enumerate(zip(*[iter(items[2:30])]*4)) if p[2]]

        # comments
        self.desc   = items[30]
        self.param  = items[31]
        self.min    = items[32]
        self.max    = items[33]
        self.notes  = items[34]

    def format(self, prop: 'Property', tblmgr: 'TableManager') -> list[str]:
        if not self.funcs:
            raise NotImplementedError(f'{self}')

        if isinstance(prop.param, str):
            if prop.param.startswith('sk'):
                prop.param = tblmgr.getSkill(prop.param).id
            else:
                raise NotImplementedError(f'{prop}')

        lines = []

        for f in self.funcs:
            itemstat = tblmgr.itemstatcost.get(f.stat)

            if itemstat is not None and itemstat.descpriority:
                prop.descpriority = max(prop.descpriority, itemstat.descpriority)
            else:
                prop.descpriority = 1000

            log('---------------------')
            log(prop)
            log()
            log(itemstat)
            log()
            log(f)
            log()

            match f.func:
                # https://d2mods.info/forum/kb/viewarticle?a=345

                case 1: # Applies a value to a stat, can use SetX parameter
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 2: # defensive function only, similar to 1 ???
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 3: # Apply the same min-max range as used in the previous function block (see res-all)
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 5: # Dmg-min related
                    lines.append(f'+{minmax(prop.min, prop.max)} {tblmgr.getString("ModStr1g")}')

                case 6: # Dmg-max related
                    lines.append(f'+{minmax(prop.min, prop.max)} {tblmgr.getString("ModStr1f")}')

                case 7: # Dmg%
                    prop.descpriority = 2000
                    lines.append(f'+{minmax(prop.min, prop.max)}% {tblmgr.getString("strModEnhancedDamage")}')

                case 8: # use for speed properties (ias, fcr, etc ...)
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 10: # skilltab skill group
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))
                    prop.descpriority = 2999

                case 11: # event-based skills
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))

                case 12: # random selection of parameters for parameter-based stat
                    lines.append('随机技能:')
                    for skillId in range(prop.min, prop.max + 1, 1):
                        assert itemstat.descfunc == 27
                        lines.append('    ' + itemstat.format(tblmgr, 0, prop.param, skillId))

                case 14: # inventory positions on item ??? (related to socket)
                    if prop.min is not None or prop.max is not None:
                        lines.append(f'{tblmgr.getString(itemstat.descstr2)} ({minmax(prop.min, prop.max, parentheses = False)})')
                    else:
                        lines.append(f'{tblmgr.getString(itemstat.descstr2)} ({prop.param})')
                    prop.descpriority = 1

                case 15: # use min field only
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 16: # use max field only
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max))

                case 17: # use param field only
                    lines.append(itemstat.format(tblmgr, param = prop.param))

                case 18: # Related to /time properties
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))

                case 19: # Related to charged item
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))

                case 20: # Simple boolean stuff. Use by indestruct
                    assert prop.min == 1
                    lines.append(tblmgr.getString('ModStre9s'))
                    prop.descpriority = 0

                case 21: # Add to group of skills, group determined by stat ID, uses ValX parameter
                    # if itemstat.descfunc is None:
                    #     offset = 0 if f.val is None else f.val
                    #     lines.append(f'+{minmax(prop.min, prop.max)} {strtbl.getOffset(itemstat.descstrpos, offset)}')
                    # else:
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, funcval = f.val))
                    prop.descpriority = 3000

                case 22: # Individual skill, using param for skill ID, random between min-max
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))

                case 23: # ethereal
                    lines.append(tblmgr.getStringByIndex(22745))
                    prop.descpriority = 0

                case 24: # property applied to character or target monster
                    lines.append(itemstat.format(tblmgr, prop.min, prop.max, prop.param))

                case _:
                    raise NotImplementedError(f'func: {f}')

            if lines[-1] is None:
                lines.pop()

        return lines

    def __str__(self) -> str:
        return '\n'.join([
            f'index = {self.index}',
            f'code  = {self.code}',
            f'funcs = {self.funcs}',
            f'desc  = {self.desc}',
            f'param = {self.param}',
            f'min   = {self.min}',
            f'max   = {self.max}',
            f'notes = {self.notes}',
        ])

class PropertyTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, PropertyTableData]

        index = 0

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')

            data = PropertyTableData(index, l)
            if data.code == 'Expansion':
                continue

            index += 1

            if data.code in self.data:
                raise NotImplementedError(f'dup: ${data.code}')

            self.data[data.code] = data

    def get(self, code: str) -> PropertyTableData:
        return self.data[code]

class ItemsStatConstTableData(TableData):
    def __init__(self, index: int, line: str):
        items = self.parse(line)

        self.index          = index
        self.stat           = items[0]
        self.op             = toInt(items[25])
        self.opparam        = toInt(items[26])
        self.opbase         = items[27]
        self.opstat1        = items[28]
        self.opstat2        = items[29]
        self.opstat3        = items[30]
        self.direct         = toInt(items[31])
        self.maxstat        = items[32]
        self.descpriority   = toInt(items[39], 0)
        self.descfunc       = toInt(items[40])
        self.descval        = toInt(items[41])
        self.descstrpos     = items[42]
        self.descstrneg     = items[43]
        self.descstr2       = items[44]
        self.dgrp           = toInt(items[45])
        self.dgrpfunc       = toInt(items[46])
        self.dgrpval        = toInt(items[47])
        self.dgrpstrpos     = items[48]
        self.dgrpstrneg     = items[49]
        self.dgrpstr2       = items[50]

    def format(self, tblmgr: 'TableManager', min = None, max = None, param = None, funcval = None) -> str:
        # https://d2mods.info/forum/kb/viewarticle?a=448

        descval = self.descval
        descstr2 = ''
        value = ''
        desc = ''

        match self.descfunc:
            case 1: # +[value] [string1]
                value = f'{minmax(min, max, sign = True)}'
                desc = tblmgr.getString(self.descstrpos)

            case 2: # [value]% [string1]
                value = f'{minmax(min, max)}%'
                desc = tblmgr.getString(self.descstrpos)

            case 3: # [value] [string1]
                if min is None and max is None:
                    value = param
                else:
                    value = minmax(min, max, sign = True)

                value = f'{value}'
                desc = tblmgr.getString(self.descstrpos)

            case 4: # +[value]% [string1]
                value = f'{minmax(min, max, sign = True)}%'
                desc = tblmgr.getString(self.descstrpos)
                descval = 1

            case 5: # [value*100/128]% [string1]
                value = f'+{minmax((min) * 100 // 128, max * 100 // 128)}%'
                desc = tblmgr.getString(self.descstrpos)

            case 6: # +[value] [string1] [string2]
                if isinstance(param, str):
                    param = tblmgr.getSkill(param).id

                value = f'+{self.execop(param)}'
                desc = tblmgr.getString(self.descstrpos)
                descstr2 = tblmgr.getString(self.descstr2)

            case 7: # [value]% [string1] [string2]
                if isinstance(param, str):
                    param = tblmgr.getSkill(param).id

                value = f'+{self.execop(param)}%'
                desc = tblmgr.getString(self.descstrpos)
                descstr2 = tblmgr.getString(self.descstr2)

            case 8: # +[value]% [string1] [string2]
                if isinstance(param, str):
                    param = tblmgr.getSkill(param).id

                value = f'+{self.execop(param)}%'
                desc = tblmgr.getString(self.descstrpos)
                descstr2 = tblmgr.getString(self.descstr2)

            case 9: # [value] [string1] [string2]
                value = f'{self.execop(param)}'
                desc = tblmgr.getString(self.descstrpos)
                descstr2 = tblmgr.getString(self.descstr2)

            case 11: # Repairs 1 Durability In [100 / value] Seconds
                if isinstance(param, str):
                    param = tblmgr.getSkill(param).id

                if self.descstr2:
                    desc = tblmgr.getString(self.descstr2) % (1, 100 // param)
                else:
                    desc = tblmgr.getString(self.descstrpos) % (100 // param)

            case 12: # +[value] [string1]
                value = f'+{minmax(min, max)}'
                desc = tblmgr.getString(self.descstrpos)

            case 13: # +[value] to [class] Skill Levels
                classId = 0 if funcval is None else funcval
                value = f'+{minmax(min, max)}'
                desc = f'{tblmgr.getClassSkillName(classId)}'
                descval = 1

            case 14: # +[value] to [skilltab] Skill Levels ([class] Only)
                skillTabId = param
                if isinstance(skillTabId, str):
                    skillTabId = tblmgr.getSkill(skillTabId).id

                classId = skillTabId // 3
                desc = f'+{minmax(min, max)} {tblmgr.getSkillTabName(skillTabId).replace("+%d", "").strip()}{tblmgr.getClassOnly(classId)}'

            case 15: # [chance]% to case [slvl] [skill] on [event]
                skillId = 0 if param is None else param
                chance = min
                skillLevel = max
                desc = tblmgr.getString(self.descstrpos) % (chance, skillLevel or 0, tblmgr.getSkillName(skillId))

            case 16: # Level [sLvl] [skill] Aura When Equipped
                descstr = tblmgr.getString(self.descstrpos).replace('%d', '%s')

                if param is None:
                    if descstr.find('%s') != -1:
                        desc = descstr % minmax(min, max)
                    else:
                        desc = descstr

                else:
                    desc = descstr % (minmax(min, max), tblmgr.getSkillName(param))

            case 17: # [value] [string1] (Increases near [time])
                # 0=day, 1=dusk, 2=night, 3=dawn

                if isinstance(param, str):
                    param = tblmgr.getSkill(param).id

                value = f'{minmax(min, max, sign = True)}'
                desc = tblmgr.getString(self.descstrpos)
                descstr2 = tblmgr.getString({
                    0: 'ModStre9e',
                    1: 'ModStre9g',
                    2: 'ModStre9d',
                    3: 'ModStre9f',
                }[param])

            case 20: # [value * -1]% [string1]
                value = f'-{minmax(min, max)}%'
                desc = tblmgr.getString(self.descstrpos)

            case 23: # [value]% [string1] [monster]:
                # TODO
                monsterId = param
                value = f'{minmax(min, max)}%'
                desc = f'{tblmgr.getString(self.descstrpos)} monsterId<{monsterId}>'
                descval = 1

            case 24: # used for charges, we all know how that desc looks
                skillId = param
                count = min
                skillLevel = max
                desc = f'{tblmgr.getString("ModStre10b")} {skillLevel} {tblmgr.getSkillName(skillId)} {tblmgr.getString(self.descstrpos) % (count, count)}'

            case 27: # +[value] to [skill] ([class] Only)
                skillId = param
                return f'+{minmax(min, max)} {tblmgr.getSkillName(skillId)}{tblmgr.getSkillClassOnly(skillId)}'

            case 28: # +[value] to [skill]
                skillId = param
                skillname = tblmgr.getSkillName(skillId)
                return f'+{minmax(min, max)} {skillname}'

            case 29: # magic bag
                return None

            case _:
                if self.descfunc is None:
                    # TODO
                    # ibp()
                    return None

                raise NotImplementedError(f'descfunc: {self.descfunc}')

        match descval:
            case 0 | None:
                return desc

            case 1:
                return f'{value} {desc}{descstr2}'.rstrip()

            case 2:
                return f'{desc} {value}{descstr2}'.rstrip()

            case _:
                raise NotImplementedError(f'unknown descval:\n{self}')

    def execop(self, param: int) -> int:
        match self.op:
            case 2:
                # adds (statvalue * basevalue) / (2 ^ param) to the opstat,
                # this does not work properly with any stat other then level because of the way this is updated,
                # it is only refreshed when you re-equip the item, your character is saved or you level up,
                # similar to passive skills, just because it looks like it works in the item description does not mean it does,
                # the game just recalculates the information in the description every frame,
                # while the values remain unchanged serverside.

                return param / (2 ** self.opparam)

            case 4:
                # this works the same way op #2 works,
                # however the stat bonus is added to the item and not to the player
                # (so that +defense per level properly adds the defense to the armor and not to the character directly!)
                return param / (2 ** self.opparam)

            case 5:
                # this works like op #4 but is percentage based,
                # it is used for percentage based increase of stats that are found on the item itself,
                # and not stats that are found on the character.
                return param / (2 ** self.opparam)

            case _:
                raise NotImplementedError(f'unknown op:\n{self}')

    def __str__(self) -> str:
        return '\n'.join([
            f'index         = {self.index}',
            f'stat          = {self.stat}',
            f'op            = {self.op}',
            f'opparam       = {self.opparam}',
            f'opbase        = {self.opbase}',
            f'opstat1       = {self.opstat1}',
            f'opstat2       = {self.opstat2}',
            f'opstat3       = {self.opstat3}',
            f'direct        = {self.direct}',
            f'maxstat       = {self.maxstat}',
            f'descpriority  = {self.descpriority}',
            f'descfunc      = {self.descfunc}',
            f'descval       = {self.descval}',
            f'descstrpos    = {self.descstrpos}',
            f'descstrneg    = {self.descstrneg}',
            f'descstr2      = {self.descstr2}',
            f'dgrp          = {self.dgrp}',
            f'dgrpfunc      = {self.dgrpfunc}',
            f'dgrpval       = {self.dgrpval}',
            f'dgrpstrpos    = {self.dgrpstrpos}',
            f'dgrpstrneg    = {self.dgrpstrneg}',
            f'dgrpstr2      = {self.dgrpstr2}',
        ])

class ItemsStatConstTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.data = {}  # type: dict[str, ItemsStatConstTableData]

        index = 0

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')
            # printList(TableData.parse(l), self.headers)

            data = ItemsStatConstTableData(index, l)
            if data.stat == 'Expansion':
                continue

            index += 1

            if data.stat in self.data:
                raise NotImplementedError(f'dup: ${data.stat}')

            self.data[data.stat] = data

    def get(self, code: str) -> ItemsStatConstTableData | None:
        return self.data.get(code)

class Property(TableData):
    def __init__(self, prop: str, param: str, min: str, max: str) -> None:
        self.prop   = prop
        self.param  = toInt(param, 0) if not param or param.isdigit() else param
        self.min    = toInt(min, 0)
        self.max    = toInt(max, 0)

        self.descpriority   = 0

    def __str__(self) -> str:
        return '\n'.join([
            f'prop  = {self.prop}',
            f'param = {self.param}',
            f'min   = {self.min}',
            f'max   = {self.max}',
        ])

class UniqueItemsTableData(TableData):
    def __init__(self, line: str):
        items = self.parse(line)
        self.index          = items[0]
        self.version        = items[1]
        self.enabled        = items[2]
        self.ladder         = items[3]
        self.rarity         = items[4]
        self.nolimit        = items[5]
        self.lvl            = toInt(items[6])
        self.lvlreq         = toInt(items[7])
        self.code           = items[8]
        self.type           = items[9]
        self.uber           = items[10]
        self.carry1         = items[11]
        self.costmult       = items[12]
        self.costadd        = items[13]
        self.chrtransform   = items[14]
        self.invtransform   = items[15]
        self.flippyfile     = items[16]
        self.invfile        = items[17]
        self.dropsound      = items[18]
        self.dropsfxframe   = items[19]
        self.usesound       = items[20]

        self.props = [Property(*p) for p in zip(*[iter(items[21:69])]*4) if p[0]]

    def __str__(self) -> str:
        return '\n'.join([
            f'index = {self.index}',
            f'code  = {self.code}',
            f'type  = {self.type}',
        ])

class UniqueItemsTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.items = []  # type: list[UniqueItemsTableData]

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')

            # printList(TableData.parse(l), self.headers)

            data = UniqueItemsTableData(l)
            if data.enabled == '' and data.version == '':
                continue

            self.items.append(data)

class RuneWordsTableData(TableData):
    def __init__(self, line: str):
        items = self.parse(line)

        self.name       = items[0]
        self.complete   = toInt(items[2])
        self.itypes     = [i for i in  items[4:10] if i]
        self.etypes     = [i for i in  items[10:14] if i]
        self.runes      = [i for i in  items[14:20] if i]
        self.props      = [Property(*p) for p in zip(*[iter(items[20:48])]*4) if p[0]]

    def __str__(self) -> str:
        return '\n'.join([
            f'name      = {self.name}',
            f'complete  = {self.complete}',
            f'itypes    = {self.itypes}',
            f'etypes    = {self.etypes}',
            f'runes     = {self.runes}',
            f'props     = {self.props}',
        ])

class RuneWordsTable:
    def __init__(self, filename: str):
        lines = loadTableFile(filename)

        self.headers = TableData.parse(lines[0].decode('UTF8'))
        self.items = []  # type: list[RuneWordsTableData]

        for l in lines[1:]:
            if not l:
                continue

            l = l.decode('cp1252')

            # printList(TableData.parse(l), self.headers)
            # raise

            data = RuneWordsTableData(l)
            if not data.complete:
                continue

            self.items.append(data)

class TableManager:
    def __init__(self):
        self.string             = StringTable('string.txt')
        self.expansionstring    = StringTable('expansionstring.txt')
        self.patchstring        = StringTable('patchstring.txt')
        self.weapons            = WeaponsTable('weapons.txt')
        self.armor              = ArmorTable('armor.txt')
        self.misc               = MiscTable('misc.txt')
        self.gems               = GemsTable('gems.txt')
        self.properties         = PropertyTable('properties.txt')
        self.itemstatcost       = ItemsStatConstTable('itemstatcost.txt')
        self.charstats          = CharStatTable('charstats.txt')
        self.skills             = SkillTable('skills.txt')
        self.skilldesc          = SkillDescTable('skilldesc.txt')

    def strip(self, s: str) -> str:
        for p in USELESS_CHARS.findall(s):
            s = s.replace(p, '')

        return s.strip()

    def getString2(self, key: str) -> str:
        for t in [self.patchstring, self.expansionstring, self.string]:
            try:
                return t.get(key)
            except KeyError:
                pass

        return None

    def getString(self, key: str) -> str:
        for t in [self.patchstring, self.expansionstring, self.string]:
            try:
                return t.get(key)
            except KeyError:
                pass

        return f'<missing string>[{key}]'

    def getStringByIndex(self, index: int) -> str:
        if 0 <= index < 10000:
            return self.string.getIndex(index)

        if 10000 <= index < 20000:
            return self.patchstring.getIndex(index - 10000)

        if 20000 <= index < 30000:
            return self.expansionstring.getIndex(index - 20000)

        raise NotImplementedError(f'invalid index: {index}')

    def getClassSkillName(self, charclass: int) -> str:
        return self.getString(self.charstats.get(charclass).allSkills)

    def getSkill(self, skillId: int | str) -> SkillTableData:
        return self.skills.get(skillId)

    def getSkillName(self, skillId: int | str) -> str:
        skill = self.getSkill(skillId)
        skdesc = self.skilldesc.get(skill.skilldesc)
        return self.getStringByIndex(skdesc.strname)

    def getSkillClassOnly(self, skillId: int) -> str:
        skill = self.skills.get(skillId)
        if skill.charclass == 0xFF:
            return ''

        return self.getClassOnly(skill.charclass)

    def getSkillTabName(self, skillTabId: int) -> str:
        classId = skillTabId // 3
        return self.getString(self.charstats.get(classId).skillTabs[int(skillTabId % 3)])

    def getClassOnly(self, classId: int) -> str:
        return self.getString(self.charstats.get(classId).classOnly)

    def getBuiltinItemType(self, code: str) -> str:
        return {
            'rwt1'  : '',       # 武器
            'rwt2'  : '',       # 装甲
            'rwt3'  : '',       # 盾牌

            'weap'  : '武器',
            'wand'  : '手杖',
            'swor'  : '剑',
            'scep'  : '权杖',
            'pole'  : '长柄武器',
            'mace'  : '钉鎚',
            'hamm'  : '铁鎚',
            'staf'  : '杖',
            'mqui'  : '十字弓(弹)',
            'miss'  : '远程武器',
            'mele'  : '近战武器',
            'h2h'   : '爪',
            'club'  : '棍棒',
            'axe'   : '斧',

            'belt'  : '腰带',
            'boot'  : '靴子',
            'glov'  : '手套',
            'helm'  : '头盔',
            'tors'  : '盔甲',

            'shie'  : '盾牌',
            'shld'  : '盾牌',
            'pala'  : '圣骑士盾牌',
        }[code]

class MarkdownHelper:
    def __init__(self, *initval: str):
        self.lines = []     # type: list[str]

        for l in initval:
            self.line(l)

    def line(self, s: str):
        self.lines.append(s)
        self.lines.append('')

    def list(self, s: str):
        self.lines.append(f'- {s}')

    def blank(self):
        if self.lines[-1] != '':
            self.lines.append('')

        self.line('<br/>')

    def color(self, s: str, color: str) -> str:
        return f'<font color={color}>{s}</font>'

    def uniqueColor(self, s: str) -> str:
        return self.color(s, '#9f8f5f')

    def text(self) -> tuple[str]:
        return self.lines

class TableParser:
    def __init__(self):
        self.tblmgr = TableManager()

    def getUniqueItemType(self, item: UniqueItemsTableData) -> str:
        if self.tblmgr.weapons.get(item.code) is not None:
            return 'weapon'

        if self.tblmgr.armor.get(item.code) is not None:
            return 'armor'

        if self.tblmgr.misc.get(item.code) is not None:
            return 'misc'

        raise NotImplementedError(f'{item}')

    def formatUniqueItem(self, item: UniqueItemsTableData) -> list[str]:
        baseItem = self.tblmgr.weapons.get(item.code)
        if baseItem is not None:
            return self.formatWeapon(item, baseItem)

        baseItem = self.tblmgr.armor.get(item.code)
        if baseItem is not None:
            return self.formatArmor(item, baseItem)

        baseItem = self.tblmgr.misc.get(item.code)
        if baseItem is not None:
            return self.formatMisc(item, baseItem)

        return []

    def formatProperty(self, prop: Property) -> list[str]:
        p = self.tblmgr.properties.get(prop.prop)
        return p.format(prop, self.tblmgr)

    def formatProperties(self, props: list[Property]) -> str:
        lines = []
        for prop in props:
            lines.extend(self.formatProperty(prop))

        return '，'.join(lines)

    def formatWeapon(self, uniqueItem: UniqueItemsTableData, baseItem: WeaponsTableData) -> list[str]:
        weapDesc = self.tblmgr.weapons.getWeaponDesc(baseItem)
        name = self.tblmgr.getString(uniqueItem.index)
        weapTypename = self.tblmgr.getString(baseItem.code)

        md = MarkdownHelper()

        md.line(f'### {md.uniqueColor(name)}')
        md.line(f'### {md.uniqueColor(weapTypename)} [`i{baseItem.index}`] [`{baseItem.code}`]')

        md.blank()

        if weapDesc is not None:
            md.line(self.tblmgr.getString(weapDesc))

        if baseItem.durability is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1d")}{baseItem.durability}')

        if baseItem.reqdex is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1f")}{baseItem.reqdex}')

        if baseItem.reqstr is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1e")}{baseItem.reqstr}')

        if uniqueItem.lvlreq is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1p")}{uniqueItem.lvlreq}')

        md.blank()

        log(f'********** {uniqueItem.index} {name} {weapTypename} *********')

        props = []
        for prop in uniqueItem.props:
            props.append([prop, self.formatProperty(prop)])
            log('\n'.join(['\n'.join(p[1]) for p in props if p[1]]))
            log()

        for p in sorted(props, reverse = True, key = lambda p: p[0].descpriority):
            if p[1]:
                descpriority = p[0].descpriority
                for p in p[1]:
                    md.line(f'{p}')

        log('\n'.join(md.text()))

        # if name.count('刮肉者'): raise

        return md.text()

    def formatArmor(self, uniqueItem: UniqueItemsTableData, baseItem: ArmorTableData) -> list[str]:
        name = self.tblmgr.getString(uniqueItem.index)
        armorTypename = self.tblmgr.getString(baseItem.code)

        md = MarkdownHelper()

        md.line(f'### {md.uniqueColor(name)}')
        md.line(f'### {md.uniqueColor(armorTypename)} [`i{baseItem.index}`] [`{baseItem.code}`]')

        md.blank()

        if baseItem.durability is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1d")}{baseItem.durability}')

        if baseItem.reqstr is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1e")}{baseItem.reqstr}')

        if baseItem.reqdex is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1f")}{baseItem.reqdex}')

        if uniqueItem.lvlreq is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1p")}{uniqueItem.lvlreq}')

        md.blank()

        log(f'********** {uniqueItem.index} {name} {armorTypename} *********')

        props = []
        for prop in uniqueItem.props:
            props.append([prop, self.formatProperty(prop)])
            log('\n'.join(['\n'.join(p[1]) for p in props if p[1]]))
            log()

        for p in sorted(props, reverse = True, key = lambda p: p[0].descpriority):
            if p[1]:
                # descpriority = p[0].descpriority
                for p in p[1]:
                    md.line(f'{p}')

        log('\n'.join(md.text()))

        # if name.count('奥罗拉的守护'): raise

        return md.text()

    def formatMisc(self, uniqueItem: UniqueItemsTableData, baseItem: MiscTableData) -> list[str]:
        # if uniqueItem.code.startswith('e*'):
        #     return []

        name = self.tblmgr.getString(uniqueItem.index)
        miscTypename = self.tblmgr.getString2(self.tblmgr.misc.get(baseItem.code).namestr)
        if miscTypename is None:
            return []

        md = MarkdownHelper()

        md.line(f'### {md.uniqueColor(name)}')
        md.line(f'### {md.uniqueColor(miscTypename)} [`i{baseItem.index}`] [`{baseItem.code}`]')

        md.blank()

        if uniqueItem.lvlreq is not None:
            md.line(f'{self.tblmgr.getString("ItemStats1p")}{uniqueItem.lvlreq}')

        md.blank()

        log(f'********** {uniqueItem.index} {name} {miscTypename} *********')

        props = []
        for prop in uniqueItem.props:
            props.append([prop, self.formatProperty(prop)])
            log('\n'.join(['\n'.join(p[1]) for p in props if p[1]]))
            log()

        for p in sorted(props, reverse = True, key = lambda p: p[0].descpriority):
            if p[1]:
                # descpriority = p[0].descpriority
                for p in p[1]:
                    md.line(f'{p}')

        log('\n'.join(md.text()))

        # if name.count('奥罗拉的守护'): raise

        return md.text()

    def formatRuneWord(self, rw: RuneWordsTableData) -> list[str]:
        name = self.tblmgr.getString(rw.name)
        itypes = '/'.join([s for s in [self.tblmgr.getBuiltinItemType(it) for it in rw.itypes] if s])
        itypes2 = ' '.join(rw.itypes)

        md = MarkdownHelper()

        t = f'{len(rw.runes)}孔 {itypes}'
        t2 = f'{itypes2}'
        md.line(f'### {md.uniqueColor(name)}')
        md.line(f'#### {md.uniqueColor(t)}')
        md.line(f'#### {md.uniqueColor(t2)}')

        md.blank()

        # md.line(f'{len(rw.runes)}孔 {itypes}')
        md.line(f'{" + ".join(rw.runes)}')

        md.blank()

        log(f'********** {name} {itypes} *********')

        props = []
        for prop in rw.props:
            props.append([prop, self.formatProperty(prop)])
            log('\n'.join(['\n'.join(p[1]) for p in props if p[1]]))
            log()

        for p in sorted(props, reverse = True, key = lambda p: p[0].descpriority):
            if p[1]:
                # descpriority = p[0].descpriority
                for p in p[1]:
                    md.line(f'{p}')

        props = []
        def formatRunesProperty(rw: RuneWordsTableData, type: str, getprops):
            md.line(f'{type}:')

            for runeCode in rw.runes:
                rune = self.tblmgr.gems.get(runeCode)
                props = self.formatProperties(getprops(rune))
                # for prop in getprops(rune):
                #     props.extend(self.formatProperty(prop))

                md.list(f'{runeCode}: {props}')

            md.blank()

        if 'rwt1' in rw.itypes:
            formatRunesProperty(rw, '武器', lambda r: r.weaponProps)

        if 'rwt2' in rw.itypes:
            formatRunesProperty(rw, '装甲', lambda r: r.helmProps)

        if 'rwt3' in rw.itypes:
            formatRunesProperty(rw, '盾牌', lambda r: r.shieldProps)

        log('\n'.join(['\n'.join(p[1]) for p in props if p[1]]))
        log()

        log('\n'.join(md.text()))

        # if name.count('财富'): ibp()

        return md.text()

def main():
    uniqueItems = UniqueItemsTable('uniqueitems.txt')
    runes = RuneWordsTable('runes.txt')
    parser = TableParser()

    tbls = {}

    try:
        for uniqueItem in uniqueItems.items:
            type = parser.getUniqueItemType(uniqueItem)
            ret = parser.formatUniqueItem(uniqueItem)
            if not ret:
                continue

            lines = tbls.setdefault(type, [])  # type: list[str]
            lines.extend(ret)
            lines.append('')
            lines.append('----------------------')
            lines.append('')

        runewords = []
        tbls['runewords'] = runewords

        for rw in runes.items:
            ret = parser.formatRuneWord(rw)
            if not ret:
                raise

            runewords.extend(ret)
            runewords.append('')
            runewords.append('----------------------')
            runewords.append('')

        itemindeies = []
        tbls['itemindex'] = itemindeies

        tblmgr = parser.tblmgr

        for tbl in [
            sorted(tblmgr.weapons.data.values(), key = lambda w: w.index),
            sorted(tblmgr.armor.data.values(), key = lambda w: w.index),
            sorted(tblmgr.misc.data.values(), key = lambda w: w.index),
        ]:
            for item in tbl:
                name = tblmgr.getString2(item.code)
                if name is None:
                    continue

                itemindeies.append(f'{item.index:>4} {name}')
    finally:
        filenames = {
            'weapon'    : '暗金武器.md',
            'armor'     : '暗金护甲.md',
            'misc'      : '暗金其他.md',
            'runewords' : '符文之语.md',
            'itemindex' : '物品ID.txt',
        }

        for type, tbl in tbls.items():
            if not tbl:
                continue

            open(r'D:\Dev\Source\sources\Diablo II\DarkMoonData\\' + filenames[type], 'wb').write('\n'.join(tbl).encode('UTF-8-SIG'))

    console.pause('done')

if __name__ == '__main__':
    Try(main)
