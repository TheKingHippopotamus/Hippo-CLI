-- טבלת חברות עם נתונים פיננסיים מלאים
-- נוצר אוטומטית מקובץ JSON

DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    ticker TEXT,
    sector TEXT,
    industry TEXT,
    description TEXT,
    exchanges TEXT,
    indices TEXT,
    last_updated TEXT,
    
    -- נתונים פיננסיים בסיסיים
    earnings BIGINT,
    ebit BIGINT,
    roe DECIMAL(10,6),
    roa DECIMAL(10,6),
    fcf BIGINT,
    equity BIGINT,
    g_stability DECIMAL(10,6),
    
    -- יחסי הערכה
    pe DECIMAL(10,6),
    peg DECIMAL(10,6),
    pb DECIMAL(10,6),
    pfcf DECIMAL(10,6),
    ps DECIMAL(10,6),
    price_to_cash DECIMAL(10,6),
    
    -- יחסי חוב
    debt_over_equity DECIMAL(10,6),
    debt_over_fcf DECIMAL(10,6),
    
    -- מרווחים
    net_margins DECIMAL(10,6),
    gross_margins DECIMAL(10,6),
    op_margins DECIMAL(10,6),
    
    -- צמיחה
    earnings_cagrr DECIMAL(10,6),
    sales_growth_yoy DECIMAL(10,6),
    sales_growth_qoq DECIMAL(10,6),
    sales_cagrr DECIMAL(10,6),
    fcf_cagrr DECIMAL(10,6),
    equity_cagrr DECIMAL(10,6),
    
    -- יציבות
    earnings_stability DECIMAL(10,6),
    earnings_growth_yoy DECIMAL(10,6),
    earnings_growth_qoq DECIMAL(10,6),
    
    -- שווי שוק ונתונים נוספים
    market_cap DECIMAL(20,2),
    revenue BIGINT,
    dividend_yield DECIMAL(10,6),
    payout_ratio DECIMAL(10,6),
    assets BIGINT,
    total_debt BIGINT,
    cash BIGINT,
    shares_outstanding BIGINT,
    ev DECIMAL(20,2),
    
    -- ציונים
    earnings_score DECIMAL(10,6),
    moat_score DECIMAL(10,6),
    safety_score DECIMAL(10,6),
    final_score DECIMAL(10,6),
    
    -- הון חוזר ויחסים נוספים
    working_capital BIGINT,
    current_ratio DECIMAL(10,6),
    gross_profit BIGINT
);

INSERT INTO companies VALUES
(1,"Apple Inc","AAPL","technology","Computer Manufacturing","Apple designs a wide variety of consumer electronic devices, including smartphones (iPhone), tablets (iPad), PCs (Mac), smartwatches (Apple Watch), AirPods, and TV boxes (Apple TV), among others. The iPhone makes up the majority of Apple's total revenue. In addition, Apple offers its customers a variety of services such as Apple Music, iCloud, Apple Care, Apple TV+, Apple Arcade, Apple Card, and Apple Pay, among others. Apple's products run internally developed software and semiconductors, and the firm is well known for its integration of hardware, software and services. Apple's products are distributed online as well as through company-owned stores and third-party retailers. The company generates roughly 40% of its revenue from the Americas, with the remainder earned internationally.","NASDAQ","SP500;DJIA;NDX","{"stock_price":1760006034034,"stock_split":1760006034034,"fundamentals":1760006034034,"additional_data":1759902049421}",99280000000,130233000000,1.5081269937718365,0.3928656540822637,96184000000,65830000000,0.9647657799216408,38.617300997670284,5.530772038203305,58.23979406119864,39.86032648931949,9.38250386796869,0.009460016540946577,1.5364575421540332,1.0515782250686185,0.26951019302188434,0.4667825022942796,0.31871030896298563,0.08979184968643805,0.09628455180293094,-0.01387388710032611,0.08342777748199182,0.07570337609529099,-0.04276149573846777,0.8958805823774413,0.09259604625139883,-0.054317998385794986,3833925643048.706,408625000000,0.004007119967977123,0.15474415793714746,331495000000,101145000000,36269000000,14856722000,3898801643048.706,0.929247941465536,NULL,0.91098851337234,NULL,-18629000000,0.8679917800453515,190739000000)
;

-- אינדקסים לשיפור ביצועי חיפוש
CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_sector ON companies(sector);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_market_cap ON companies(market_cap);
CREATE INDEX idx_companies_revenue ON companies(revenue);
CREATE INDEX idx_companies_pe ON companies(pe);
CREATE INDEX idx_companies_roe ON companies(roe);

-- סטטיסטיקות
SELECT 'Total companies: ' || COUNT(*) as stats FROM companies;
SELECT 'Companies with tickers: ' || COUNT(*) as stats FROM companies WHERE ticker IS NOT NULL;
SELECT 'Companies by sector: ' || sector || ' (' || COUNT(*) || ')' as stats FROM companies GROUP BY sector ORDER BY COUNT(*) DESC LIMIT 10;

