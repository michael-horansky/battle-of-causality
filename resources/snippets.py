# When ordering priority based on subsets of length sums

ssetup = 5
sprogen = 3
saction = 7

did_we_fail = False
for number_of_effect_deactivations in range(sprogen+saction+1):
    for number_of_stone_deactivations in range(ssetup + min(sprogen, number_of_effect_deactivations) + 1):
        # We use the fact that all setup stones have a lower recency than effect-progenitor stones
        for number_of_progenitor_effect_deactivations in range(max(max(0, number_of_stone_deactivations - ssetup), number_of_effect_deactivations - saction), min(min(sprogen, number_of_stone_deactivations), number_of_effect_deactivations) + 1):
            print(f"-------------- {number_of_effect_deactivations}, {number_of_stone_deactivations}, {number_of_progenitor_effect_deactivations} -------------")
            print(f"currently deactivating {number_of_effect_deactivations - number_of_progenitor_effect_deactivations} actions out of {saction}")
            print(f"currently deactivating {number_of_progenitor_effect_deactivations} progenitors out of {sprogen}")
            print(f"currently deactivating {number_of_stone_deactivations - number_of_progenitor_effect_deactivations} setups out of {ssetup}")
            if number_of_effect_deactivations - number_of_progenitor_effect_deactivations > saction:
                did_we_fail = True
            if number_of_progenitor_effect_deactivations > sprogen:
                did_we_fail = True
            if number_of_stone_deactivations - number_of_progenitor_effect_deactivations > ssetup:
                did_we_fail = True
if did_we_fail:
    print("This is so over")
else:
    print("We are biden back")
