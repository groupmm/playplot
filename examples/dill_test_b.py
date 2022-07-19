from dill import load

with open("dill_pickle.pck", 'rb') as f:
    test = load(f)

    print(test(2))
