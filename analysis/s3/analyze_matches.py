import json
import csv
from collections import defaultdict

# 读取match_id_mapping.csv，统计每支队伍的弃权场次
team_forfeits = {}
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/match_id_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        team = row[0]
        forfeit_count = sum(1 for m in row[1:] if m == '-')
        team_forfeits[team] = forfeit_count

# 定义弃权队伍（最后6支队伍中除了Jurmac的其他队伍）
forfeit_teams = {'唐仁国', '秽土转生/donk干拉', '有请下一队', '暴打说书人', 'IECS'}

# 读取matches.json
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/matches.json', 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

# 假设matches_data是列表，每个元素是{"result": {...}}
matches = [m['result'] for m in matches_data]

# 构建player到nickname的映射
player_nicknames = {}
for match in matches:
    if 'playersInfo' in match:
        for uid, info in match['playersInfo'].items():
            player_nicknames[uid] = info['nickname']

# 构建player-team统计
player_team_stats = defaultdict(lambda: defaultdict(list))

# 队伍净胜分
team_net_wins = defaultdict(int)

# 队伍胜场数
team_wins = defaultdict(int)

# 官方队伍净胜分
official_team_net_wins = defaultdict(int)

# 官方队伍胜场数
official_team_wins = defaultdict(int)

name_mapping = {
    'happycs3': 'happycs3',
    'donk干拉': '秽土转生/donk干拉',
    'mirsir': 'Mirsir',
    'NYLOO': 'NYLOO',
    'Jurmac': 'Jurmac',
    '穷则独善其身': '穷则独善其身',
    '有请下一队': '有请下一队',
    '一分够了': '一分够了',
    'DP 7.0': 'DP7.0',
    '66574quad': '66574quad',
    '圣盾嘲讽': '圣盾嘲讽',
    'IECS': 'IECS',
    '这是什么体系': '这是什么体系',
    '枪哥爷爷': '枪哥爷爷',
    '卡皮哈皮': '卡皮哈皮',
    '熊猫人': '熊猫人',
    'Nessie Hunter': 'Nessie Hunters',
    '佰日萌新': '佰日萌新',
    '唐仁国': '唐仁国',
    '仙阁': '仙阁',
    'DP7.0': 'DP7.0',
    '枪哥二爷爷': '枪哥二爷爷',
    'sync squad': 'Sync squad',
    '10个188再别说了': '10个188再别说了',
    '圣盾嘲讽复生冲锋': '圣盾嘲讽',
    '枪之遗址': '枪之遗址',
    '暴打说书人': '暴打说书人',
    'sync': 'Sync squad',
    '秽土转生': '秽土转生/donk干拉',
    '10个188': '10个188再别说了',
    'nessie hunter': 'Nessie Hunters',
    'hpcs3': 'happycs3',
    'jurmac': 'Jurmac',
    '圣盾嘲讽复苏冲锋': '圣盾嘲讽',
    'Dry Peek 7.0': 'DP7.0',
    'dry peek 7.0': 'DP7.0',
    'Mirsir': 'Mirsir',
    'Sync Squad': 'Sync squad',
    'nyloo': 'NYLOO',
    'Nyloo': 'NYLOO',
}

player_mapping = {
    '76561199507140552': '76561198981634081'
}

for match in matches:
    base = match['baseInfo']
    t_team = match['t_team_info']['name']
    ct_team = match['ct_team_info']['name']
    t_wins = int(base['t_win_times'])
    ct_wins = int(base['ct_win_times'])

    # 更新净胜分
    team_net_wins[t_team] += t_wins - ct_wins
    team_net_wins[ct_team] += ct_wins - t_wins

    # 更新胜场数
    if t_wins > ct_wins:
        team_wins[t_team] += 1
    elif ct_wins > t_wins:
        team_wins[ct_team] += 1

    # 映射到官方名称
    t_team_official = name_mapping.get(t_team, t_team)
    ct_team_official = name_mapping.get(ct_team, ct_team)

    # 更新官方净胜分
    official_team_net_wins[t_team_official] += t_wins - ct_wins
    official_team_net_wins[ct_team_official] += ct_wins - t_wins

    # 更新官方胜场数
    if t_wins > ct_wins:
        official_team_wins[t_team_official] += 1
    elif ct_wins > t_wins:
        official_team_wins[ct_team_official] += 1

    # 处理players
    for camp, players in [('T', match.get('Tplayers', {})), ('CT', match.get('CTplayers', {}))]:
        team_name = name_mapping[t_team if camp == 'T' else ct_team]
        for uid, stats in players.items():
            if uid in player_mapping:
                uid = player_mapping[uid]
            player_team_stats[uid][team_name].append(stats)

# 处理弃权情况
for team, forfeit_count in team_forfeits.items():
    if forfeit_count > 0:
        if team in forfeit_teams:
            # 弃权队伍：每场记录为0:13失败
            official_team_net_wins[team] += forfeit_count * (0 - 13)
            # 胜场数不变（失败）
        else:
            # 非弃权队伍：每场记录为13:0胜利
            official_team_net_wins[team] += forfeit_count * (13 - 0)
            official_team_wins[team] += forfeit_count

# 计算player统计
player_rows = []
for uid, teams in player_team_stats.items():
    nickname = player_nicknames.get(uid, 'Unknown')
    for team_name, games in teams.items():
        num_games = len(games)
        avg_rating = sum(float(g['pw_rating']) for g in games) / num_games
        # 其他统计，比如平均kill, death等
        avg_kill = sum(int(g['kill']) for g in games) / num_games
        avg_death = sum(int(g['death']) for g in games) / num_games
        avg_assist = sum(int(g['assist']) for g in games) / num_games
        avg_adr = sum(int(g['adpr']) for g in games) / num_games
        
        # 新增场均统计
        avg_rws = sum(float(g['rws']) for g in games) / num_games
        avg_first_kill = sum(int(g['first_kill']) for g in games) / num_games
        avg_trade_count = sum(int(g['trade_count']) for g in games) / num_games
        avg_first_death = sum(int(g['first_death']) for g in games) / num_games
        avg_trade_frag_count = sum(int(g['trade_frag_count']) for g in games) / num_games
        avg_is_mvp = sum(int(g['is_mvp']) for g in games)
        avg_mvp_count = sum(int(g['mvp_count']) for g in games) / num_games
        avg_1v1 = sum(int(g['1v1']) for g in games) / num_games
        avg_1v2 = sum(int(g['1v2']) for g in games) / num_games
        avg_1v3 = sum(int(g['1v3']) for g in games) / num_games
        avg_1v4 = sum(int(g['1v4']) for g in games) / num_games
        avg_1v5 = sum(int(g['1v5']) for g in games) / num_games
        avg_1vn = (avg_1v1 + avg_1v2 + avg_1v3 + avg_1v4 + avg_1v5)
        avg_awp_kill_num = sum(int(g['awp_kill_num']) for g in games) / num_games

        # 可以添加更多
        player_rows.append({
            '用户ID': uid,
            '昵称': nickname,
            '队伍名称': team_name,
            '场次': num_games,
            '平均Rating': round(avg_rating, 2),
            '平均击杀': round(avg_kill, 2),
            '平均死亡': round(avg_death, 2),
            '平均助攻': round(avg_assist, 2),
            '平均伤害': round(avg_adr, 2),
            '平均RWS': round(avg_rws, 2),
            '平均首杀': round(avg_first_kill, 2),
            '平均换命次数': round(avg_trade_count, 2),
            '平均首死': round(avg_first_death, 2),
            '平均换命击杀数': round(avg_trade_frag_count, 2),
            '总MVP次数': round(avg_is_mvp, 2),
            '平均MVP计数': round(avg_mvp_count, 2),
            '平均1v1': round(avg_1v1, 2),
            '平均1v2': round(avg_1v2, 2),
            '平均1v3': round(avg_1v3, 2),
            '平均1v4': round(avg_1v4, 2),
            '平均1v5': round(avg_1v5, 2),
            '平均残局数': round(avg_1vn, 2),
            '平均AWP击杀数': round(avg_awp_kill_num, 2)
        })

# 写入players.csv
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/players.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['用户ID', '昵称', '队伍名称', '场次', '平均Rating', '平均击杀', '平均死亡', '平均助攻', '平均伤害', '平均RWS', '平均首杀', '平均换命次数', '平均首死', '平均换命击杀数', '总MVP次数', '平均MVP计数', '平均1v1', '平均1v2', '平均1v3', '平均1v4', '平均1v5', '平均残局数', '平均AWP击杀数'])
    writer.writeheader()
    writer.writerows(player_rows)

# 队伍CSV：队伍名称, 胜场数, 净胜分
team_rows = [{'team': team, 'wins': official_team_wins[team], 'net_wins': net} for team, net in official_team_net_wins.items()]

# 排序：先胜场数降序，后净胜分降序
team_rows = sorted(team_rows, key=lambda x: (-x['wins'], -x['net_wins']))

with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/teams.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['team', 'wins', 'net_wins'])
    writer.writeheader()
    writer.writerows(team_rows)

# 读取match_id_mapping.csv 获取官方队伍名称
official_team_names = set()
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/match_id_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        official_team_names.add(row[0])

# 构建match_id到match的映射
match_dict = {match['baseInfo']['match']: match for match in matches}

# 读取match_id_mapping.csv，获取队伍顺序和match_ids
team_order = []
team_match_ids = {}
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/match_id_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        team = row[0]
        team_order.append(team)
        team_match_ids[team] = row[1:]

# 计算最大比赛数
max_scores = max(len(team_match_ids[team]) for team in team_order)

# 准备fieldnames
fieldnames = ['team'] + [f'score_{i}' for i in range(1, max_scores + 1)] + ['wins', 'net_wins']

# 准备rows
rows = []
for team in team_order:
    scores = []
    for mid in team_match_ids[team]:
        if mid == '-':
            if team in forfeit_teams:
                scores.append('0:13')
            else:
                scores.append('13:0')
        else:
            match = match_dict[mid]
            t_team = match['t_team_info']['name']
            ct_team = match['ct_team_info']['name']
            t_team_official = name_mapping.get(t_team, t_team)
            ct_team_official = name_mapping.get(ct_team, ct_team)
            t_wins = int(match['baseInfo']['t_win_times'])
            ct_wins = int(match['baseInfo']['ct_win_times'])
            official_team = name_mapping.get(team, team)
            if official_team == t_team_official:
                scores.append(f'{t_wins}:{ct_wins}')
            elif official_team == ct_team_official:
                scores.append(f'{ct_wins}:{t_wins}')
            else:
                scores.append('error')  # 不应该发生
    official_team = name_mapping.get(team, team)
    wins = official_team_wins.get(official_team, 0)
    net_wins = official_team_net_wins.get(official_team, 0)
    row = {'team': team, 'wins': wins, 'net_wins': net_wins}
    for i, score in enumerate(scores):
        row[f'score_{i+1}'] = score
    rows.append(row)

# 写入team_details.csv
with open('/home/lemon/PycharmProjects/thucs2pl/analysis/s3/team_details.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
