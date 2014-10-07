from web import db
from web.models import Chain, Location

if __name__ == '__main__':
    # Migration adding initial DB records for Chain and Location
    stout = Chain('Stout')
    stout_hollywood = Location('Hollywood', 'http://www.stoutburgersandbeers.com/hollywood-beer-menu/', stout)
    stout_studio_city = Location('Studio City', 'http://www.stoutburgersandbeers.com/studio-city-beer-menu/', stout)
    stout_santa_monica = Location('Santa Monica', 'http://www.stoutburgersandbeers.com/santa-monica-beer-menu/', stout)

    ball_and_chain = Chain('Ball and Chain')
    bandc_hollywood = Location('Hollywood', 'http://www.ball-and-chain-restaurant.com/', ball_and_chain)

    db.session.add(stout)
    db.session.add(stout_hollywood)
    db.session.add(stout_studio_city)
    db.session.add(stout_santa_monica)
    db.session.add(ball_and_chain)
    db.session.add(bandc_hollywood)
    db.session.commit()
