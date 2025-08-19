def get_world_question_score(per_scores, world_wrong_score):
    mode_a = 0  # sum of all previous correct answers
    mode_b = set()  # scores where at least one previous was not correct
    
    for score in per_scores:
        new_mode_b = set()
        # From mode_a: can choose wrong or skip (both go to mode_b)
        new_mode_b.add(mode_a + world_wrong_score)
        new_mode_b.add(mode_a + 0)
        # From existing mode_b: can choose correct (0), wrong, or skip
        for x in mode_b:
            new_mode_b.add(x + 0)
            new_mode_b.add(x + world_wrong_score)
        mode_b = new_mode_b
        # Update mode_a (only if correct is chosen)
        mode_a += score
    
    total_scores = {mode_a} | mode_b
    return total_scores, len(total_scores)


def get_world_question_score_true_table(per_scores, world_wrong_score):
    n = len(per_scores)
    states = ['C', 'W', 'S']
    from itertools import product

    truth_table = []
    score_set = set()

    for case in product(states, repeat=n):
        total_score = 0
        all_previous_correct = True
        case_str = ''.join(case)
        case_scores = []

        for i in range(n):
            if case[i] == 'S':
                case_scores.append(0)
                all_previous_correct = False
            elif case[i] == 'W':
                case_scores.append(world_wrong_score)
                all_previous_correct = False
            elif case[i] == 'C':
                if all_previous_correct:
                    case_scores.append(per_scores[i])
                else:
                    case_scores.append(0)
            total_score += case_scores[-1]

        truth_table.append((case_str, case_scores, total_score))
        score_set.add(total_score)

    # Print truth table
    print("Truth Table:")
    print("Case | Scores | Total")
    print("---------------------")
    for case, scores, total in truth_table:
        print(f"{case} | {scores} | {total}")

    return score_set,len(score_set)


def count_possible_scores(total_option_questions, correct_score, no_answer_score, wrong_score, 
                         total_world_questions, per_scores, world_wrong_score):
    possible_scores = set()

    # 处理选择题部分
    option_scores = set()
    for a in range(total_option_questions + 1):  # 答对的题数
        for b in range(total_option_questions - a + 1):  # 不答的题数
            c = total_option_questions - a - b  # 答错的题数
            total = correct_score * a + no_answer_score * b + wrong_score * c
            option_scores.add(total)

    # 处理应用题部分
    world_scores = set()
    if total_world_questions > 0 and per_scores:
        # 每个应用题的小问得分情况
        single_world_scores, _ = get_world_question_score(per_scores, world_wrong_score)
        # print(single_world_scores, _)
        # 多个应用题的得分是单个应用题得分的和的可能组合
        world_scores = {0}
        for _ in range(total_world_questions):
            temp = set()
            for s in world_scores:
                for ws in single_world_scores:
                    temp.add(s + ws)
            world_scores = temp
    else:
        world_scores = {0}

    # 组合选择题和应用题的得分
    for os in option_scores:
        for ws in world_scores:
            total = os + ws
            if total < 0:
                total = 0
            possible_scores.add(total)

    return len(possible_scores)


if __name__ == "__main__":
    # print(get_world_question_score([1,2,3], -1))
    # print(get_world_question_score_true_table([1,2,3], -1))

    print(count_possible_scores(
        8, 5, -1, -3,
        total_world_questions=0,
        per_scores=[2, 3, 1],  # 每个应用题有3小问，分值分别为2, 3, 1
        world_wrong_score = -1
    ))

    # 问题：
    # 某次数学竞赛共有total_option_questions道选择题和total_world_questions道应用题，每道选择题答对得correct_score分，不答得no_answer_score分，答错得wrong_score分；每道应用题又分为len(per_scores)小问，每小问的分值依次为per_scores[0], per_scores[1], ...分。小问不作答不得分，做错了得world_wrong_score分，需要注意，只有之前小问做对了，当前小问做对才能得分，否则，即使当前小问做对了也不得分。当总分出现负值时，阅卷系统将自动把总分归为零分，则共有多少种不同的总分？
