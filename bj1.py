import random
import math

# ---------- CONFIG ----------
NUM_DECKS = 6      
RESHUFFLE_PENETRATION = 0.25  
MAX_RESPLITS = 3  
STARTING_BALANCE = 1000

suits=['♠', '♥', '♦', '♣']
ranks=['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
card_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

def makeShoe(num_decks=NUM_DECKS):
    shoe = [(rank, suit) for _ in range(num_decks) for rank in ranks for suit in suits]
    random.shuffle(shoe)
    return shoe

def dealCard(shoe):
    if not shoe:
        raise RuntimeError("Shoe is empty — should have been reshuffled earlier.")
    return shoe.pop()

def showHand(hand):
    return ' '.join(f"{r}{s}" for r, s in hand)

def calcScore(hand):
    score = sum(card_values[card[0]] for card in hand)
    aces = sum(1 for card in hand if card[0] == 'A')
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def is_blackjack(hand):
    return len(hand) == 2 and calcScore(hand) == 21

def enough_funds(balance, required):
    return balance >= required

def input_int(prompt, minv=None, maxv=None):
    while True:
        try:
            v = int(input(prompt))
            if minv is not None and v < minv:
                print(f"Must be at least {minv}.")
                continue
            if maxv is not None and v > maxv:
                print(f"Must be at most {maxv}.")
                continue
            return v
        except ValueError:
            print("Please enter a valid integer.")


def play_blackjack():
    balance = STARTING_BALANCE
    stats = {
        'Rounds': 0, 'Wins': 0, 'Losses': 0, 'Pushes': 0, 'Blackjacks': 0
    }
    shoe = makeShoe()
    min_shoe_size = NUM_DECKS * 52 * RESHUFFLE_PENETRATION

    print("---- Welcome to Casino Blackjack ----")
    print(f"Starting balance: ${balance}\n")

    while True:
        if balance <= 0:
            print("You're broke — game over.")
            break
        # Reshuffle shoe if low
        if len(shoe) < min_shoe_size:
            print("\n*** Reshuffling shoe ***\n")
            shoe = makeShoe()

        print("-" * 46)
        print(f"Balance: ${balance}")
        bet = input_int(f"Place your bet (1 - {balance}): $", 1, balance)
        # Reserve the bet now (stake holding)
        balance -= bet
        # initial deal
        player_hand = [dealCard(shoe), dealCard(shoe)]
        dealer_hand = [dealCard(shoe), dealCard(shoe)]

        print(f"\nYou: {showHand(player_hand)} (score: {calcScore(player_hand)})")
        print(f"Dealer: {dealer_hand[0][0]}{dealer_hand[0][1]} [hidden]")

        # immediate blackjack check
        if is_blackjack(player_hand):
            print("\n-- Player has Blackjack! --")
            if is_blackjack(dealer_hand):
                print(f"Dealer: {showHand(dealer_hand)} (Blackjack) -> Push.")
                balance += bet  
                stats['pushes'] += 1
            else:
                # player wins 3:2 (profit = 1.5*bet)
                profit = int(math.floor(bet * 1.5))
                balance += bet + profit
                stats['Wins'] += 1
                stats['Blackjacks'] += 1
                print(f"You win Blackjack! Payout: 3:2 -> profit ${profit}")
            stats['Rounds'] += 1
 
            again = input("\nPlay again? (y/n): ").lower()
            if again != 'y':
                break
            else:
                continue

    
        hands = [player_hand]
        bets = [bet]  
        hand_results = [None] * (MAX_RESPLITS + 1)  

        # Splitting process 
        i = 0
        while i < len(hands):
            hand = hands[i]
            # check if can split
            rank0 = hand[0][0]
            rank1 = hand[1][0] if len(hand) >= 2 else None
            can_split = (len(hand) == 2 and rank0 == rank1 and len(hands) <= MAX_RESPLITS)
            if can_split:
                # ask player whether to split this hand
                print(f"\nHand {i+1}: {showHand(hand)} (split available)")
                # check funds to place another equal bet for this split
                if not enough_funds(balance, bets[i]):
                    print("Insufficient funds to split this hand. Skipping split.")
                    i += 1
                    continue
                ans = input("Do you want to split this pair? (y/n): ").lower()
                if ans == 'y':
                    # perform split: create two hands from the pair
                    # deduct new stake now (reserve)
                    balance -= bets[i]
                    card_a = hand[0]
                    card_b = hand[1]
                    # new hands: each gets original card + one new card
                    new_hand1 = [card_a, dealCard(shoe)]
                    new_hand2 = [card_b, dealCard(shoe)]
                    hands[i] = new_hand1
                    hands.insert(i + 1, new_hand2)
                    # bets: duplicate bet for second hand
                    bets[i] = bets[i]  # unchanged for first
                    bets.insert(i + 1, bets[i])
                    print(f"Split -> Hand {i+1}: {showHand(hands[i])} | Hand {i+2}: {showHand(hands[i+1])}")
                    
                    i += 1
                    continue  # re-evaluate current index (hand now modified)
                else:
                    i += 1
                    continue
            else:
                i += 1

        
        hand_outcomes = []  # store tuples (result_str, bet_change) where bet_change already applied to balance earlier (we reserved), so we'll add/subtract accordingly
        for h_index, hand in enumerate(hands, start=1):
            print(f"\n---- Playing Hand {h_index} ----")
            # special rule: if hand originated from split Aces (first two cards contain A and was split), policy: one card only; treat as stand after one draw
            is_split_aces = False
            if len(hand) == 2 and hand[0][0] == 'A' and hand[1][0] != hand[0][0]:
                # We'll check: if first card is Ace and second card was dealt from deck directly after split and no further action allowed.
                pass
            doubled = False
            hand_bet = bets[h_index - 1]

            if len(hand) == 2 and calcScore(hand) == 21:
                print(f"Hand {h_index} shows 21 (from initial two cards). Treated as 21 (not blackjack after splits).")
                # skip actions -> will resolve later
            else:
                while True:
                    score = calcScore(hand)
                    print(f"Player hand: {showHand(hand)} (score: {score})")
                    print(f"Dealer shows: {dealer_hand[0][0]}{dealer_hand[0][1]} [hidden]")

                    if score > 21:
                        print(" -> Busted!")
                        break
                    # check if doubling is allowed: only on first 2 cards typically (we allow after split too)
                    can_double = (len(hand) == 2)
                    if len(hand) == 2 and hand[0][0] == 'A' and hand[1][0] != hand[0][0]:
                        pass

                    # present options
                    options = "(h)it, (s)tand"
                    if can_double and enough_funds(balance, hand_bet):
                        options += ", (d)ouble"
                    choice = input(f"Choose {options}: ").lower().strip()
                    if choice == 'h':
                        newc = dealCard(shoe)
                        hand.append(newc)
                        print(f"You draw: {newc[0]}{newc[1]}")
                        # loop to show updated
                        continue
                    elif choice == 'd' and can_double and enough_funds(balance, hand_bet):
                        # Deduct extra stake now (double)
                        balance -= hand_bet
                        hand_bet *= 2
                        bets[h_index - 1] = hand_bet  # update stored bet
                        newc = dealCard(shoe)
                        hand.append(newc)
                        print(f"You double and draw: {newc[0]}{newc[1]}")
                        doubled = True
                        # automatically stand after double
                        break
                    else:
                        # stand
                        break
            # end of actions for this hand
            hand_outcomes.append({'hand': hand, 'bet': bets[h_index - 1], 'doubled': doubled})

        # Dealer plays if at least one player hand still alive (not busted)
        any_live = any(calcScore(hdata['hand']) <= 21 for hdata in hand_outcomes)
        print("\nDealer reveals: ", showHand(dealer_hand), f"(score: {calcScore(dealer_hand)})")
        if any_live:
            while True:
                score = calcScore(dealer_hand)
                contains_ace = any(card[0] == 'A' for card in dealer_hand)
                raw_score = sum(card_values[c[0]] for c in dealer_hand)
                soft = (contains_ace and raw_score == 17 + 10) 
                # Better detection for soft 17:
                min_score = sum(1 if c[0] == 'A' else card_values[c[0]] for c in dealer_hand)
                has_soft = False
                if any(c[0] == 'A' for c in dealer_hand):
                    # if counting one Ace as 11 doesn't bust => soft
                    if min_score + 10 <= 21:
                        has_soft = (min_score + 10 == score)
                if score < 17:
                    newc = dealCard(shoe)
                    dealer_hand.append(newc)
                    print(f"Dealer draws: {newc[0]}{newc[1]}")
                    continue
                elif score == 17 and has_soft:
                    # stands on soft 17 per configuration
                    break
                else:
                    break
        dealer_score = calcScore(dealer_hand)
        print(f"Dealer final: {showHand(dealer_hand)} (score: {dealer_score})")

        stats['Rounds'] += 1
        for idx, hinfo in enumerate(hand_outcomes, start=1):
            hand = hinfo['hand']
            hb = hinfo['bet']
            hscore = calcScore(hand)
            print(f"\n-- Resolving Hand {idx}: {showHand(hand)} (score: {hscore}) | Bet: ${hb} --")
            if hscore > 21:
                print("Result: BUST -> lose bet.")
                stats['Losses'] += 1
                # lost stake already reserved so nothing to deduct (we deducted initially and on resplits/doubles)
                # no balance change here (stake was already removed)
            else:
                # dealer busted or player higher -> win
                if dealer_score > 21:
                    print("Result: Dealer busted -> You win this hand.")
                    balance += (hb * 2)  # return stake + profit equal to stake
                    stats['Wins'] += 1
                else:
                    if hscore > dealer_score:
                        print("Result: You beat dealer -> win.")
                        balance += (hb * 2)
                        stats['Wins'] += 1
                    elif hscore < dealer_score:
                        print("Result: Dealer wins -> you lose stake.")
                        stats['Losses'] += 1
                        # stake already taken
                    else:
                        print("Result: Push -> stake returned.")
                        balance += hb  # return stake
                        stats['Pushes'] += 1

        print(f"\nBalance after round: ${balance}")
        print(f"Stats (Rounds/Wins/Losses/Pushes/Blackjacks): {stats['Rounds']}/{stats['Wins']}/{stats['Losses']}/{stats['Pushes']}/{stats['Blackjacks']}")

        if balance <= 0:
            print("You're out of money. Game over.")
            break

        again = input("\nPlay again? (y/n): ").lower().strip()
        if again != 'y':
            print("Thanks for playing! Final stats:")
            print(stats)
            break


if __name__ == "__main__":
    play_blackjack()
