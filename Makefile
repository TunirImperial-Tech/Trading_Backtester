data_pipeline: 
	python src/data_pipeline.py

test_backtest:
	python -m tests.test_backtester

dashboard:
	streamlit run src/dashboard.py