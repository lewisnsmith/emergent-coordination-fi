from flock.core.types import Decision, Order


def test_decision_net_action():
    buy = Decision("a", 0, (Order("X", "buy", 10),))
    sell = Decision("a", 0, (Order("X", "sell", 10),))
    hold = Decision("a", 0, ())
    offset = Decision("a", 0, (Order("X", "buy", 5), Order("Y", "sell", 5)))
    assert buy.action == "buy"
    assert sell.action == "sell"
    assert hold.action == "hold"
    assert offset.action == "hold"
