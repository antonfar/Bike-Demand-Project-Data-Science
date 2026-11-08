# Context for selected failures

These cases were selected after inspecting the original test errors. They are
exploratory explanations, not causal estimates. Weather/service context is not
fed back into the forecasting models. All observations remain in headline scores.

## October 29–30, 2012: Sandy and service availability

The model predicted 5,861.7 rentals on October 29; the dataset records 22.
On October 30, the prediction was 4,918.9 versus 1,096 recorded rentals.

ARLnow's October 31 reporting says Capital Bikeshare suspended service for about
36 hours during Sandy and resumed Tuesday afternoon (October 30). Its report
includes comments from BikeArlington's Chris Eatough. A DC government notice
also confirms government and school closures for October 30 because of Sandy.

Interpretation: the service shutdown is directly relevant context for very low
recorded rentals. Counts measure realized use under service availability, not
unconstrained customer demand. These sources do not establish why the source
dataset contains exactly 22 rentals or permit separating every cause of the drop.
We have not reconstructed a complete time-stamped closure-information feed.

Sources:
- Katie Pyzyk, ARLnow, October 31, 2012:
  https://www.arlnow.com/2012/10/31/bikeshare-fares-well-but-cyclists-cautioned-of-hazards/
- DC government, October 29, 2012, announcement for October 30:
  https://osse.dc.gov/ko/node/366322

## December 24, 2012: rain during the holiday period

Prediction: 4,063.7; recorded rentals: 920. The National Weather Service's
December 2012 storm report says rain affected the Washington DC metro on
December 24 (pages 2–3). The source data mark this date as a working day and
not an official holiday. That binary label does not capture the entire holiday
period. Reduced holiday travel is a hypothesis, not a measured explanation.

## December 26, 2012: regional winter weather

Prediction: 3,601.8; recorded rentals: 441. The National Weather Service documents
winter weather from December 26–27 in northern Virginia, including Arlington and
Fairfax, with sleet/freezing rain and snow at higher elevations (page 4). This is
regional context, not a station-level measurement or proof of a full-system
closure. Weather, holiday patterns and other factors may overlap.

Source for December cases:
- National Weather Service, Storm Data and Unusual Weather Phenomena,
  December 2012, pages 2–4, printed April 29, 2013:
  https://www.weather.gov/media/lwx/stormdata/2012/storm1212.pdf

All web sources accessed November 6, 2026. No event-specific override has been
added to the original model. A future study would need archived forecast weather
and service-status announcements with publication timestamps.
