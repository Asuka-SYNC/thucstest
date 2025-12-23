import json
import csv
from collections import defaultdict

# 读取matches.json
with open('matches.json', 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

# 假设matches_data是列表，每个元素是{"result": {...}}
matches = [m['result'] for m in matches_data]

# 构建player到nickname的映射
player_nicknames = {}
player_stats = {}
player_mapping = {
    '76561199179588151': '76561198817729950'
}


def escape_nickname(nickname):
    return f' {nickname.replace(',', '，')}'


def main():
    for match in matches:
        if 'playersInfo' in match:
            for uid, info in match['playersInfo'].items():
                uid = player_mapping.get(uid, uid)
                player_nicknames[uid] = escape_nickname(info['nickname'])
                player_stats[uid] = []

    for match in matches:
        base = match['baseInfo']
        t_team = match['t_team_info']['name']
        ct_team = match['ct_team_info']['name']
        t_wins = int(base['t_win_times'])
        ct_wins = int(base['ct_win_times'])
        mvp_rating, mvp_uid = None, None
        # 处理players
        for camp, players in [('T', match.get('Tplayers', {})), ('CT', match.get('CTplayers', {}))]:
            camp_win = (t_wins > ct_wins and camp == 'T') or (ct_wins > t_wins and camp == 'CT')
            for uid, stats in players.items():
                uid = player_mapping.get(uid, uid)
                stats['is_win'] = camp_win
                player_stats[uid].append(stats)
                stats['is_mvp'] = 0  # 先标记为非MVP
                if stats['pw_rating'] is not None:
                    if mvp_rating is None or float(stats['pw_rating']) > mvp_rating:
                        mvp_rating = float(stats['pw_rating'])
                        mvp_uid = uid

        # 标记MVP
        player_stats[mvp_uid][-1]['is_mvp'] = 1

    # 计算player统计
    player_rows = []
    for uid, games in player_stats.items():
        nickname = player_nicknames.get(uid, 'Unknown')
        num_games = len(games)
        win_games = sum(1 for g in games if g['is_win'])
        mvp_counts = sum(int(g['is_mvp']) for g in games)
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
        avg_mvp_count = sum(int(g['mvp_count']) for g in games) / num_games
        avg_1v1 = sum(int(g['1v1']) for g in games) / num_games
        avg_1v2 = sum(int(g['1v2']) for g in games) / num_games
        avg_1v3 = sum(int(g['1v3']) for g in games) / num_games
        avg_1v4 = sum(int(g['1v4']) for g in games) / num_games
        avg_1v5 = sum(int(g['1v5']) for g in games) / num_games
        avg_1vn = (avg_1v1 + avg_1v2 + avg_1v3 + avg_1v4 + avg_1v5)
        avg_awp_kill_num = sum(int(g['awp_kill_num']) for g in games) / num_games

        score = 1000 - 7 * num_games + 20 * win_games + 5 * mvp_counts

        # 可以添加更多
        player_rows.append({
            '用户ID': uid,
            '昵称': nickname,
            '积分': score,
            '场次': num_games,
            '胜场': win_games,
            '胜率': f'{round(win_games / num_games * 100, 2)}%',
            'mvp场次': mvp_counts,
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
    with open('players.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f,
                                fieldnames=['用户ID', '昵称', '积分', '场次', '胜场', '胜率', 'mvp场次', '平均Rating',
                                            '平均击杀', '平均死亡',
                                            '平均助攻', '平均伤害', '平均RWS', '平均首杀', '平均换命次数', '平均首死',
                                            '平均换命击杀数', '平均MVP计数', '平均1v1', '平均1v2',
                                            '平均1v3', '平均1v4', '平均1v5', '平均残局数', '平均AWP击杀数'])
        writer.writeheader()
        writer.writerows(player_rows)


if __name__ == '__main__':
    main()
