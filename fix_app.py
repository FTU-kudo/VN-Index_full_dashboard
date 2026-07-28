import re

with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

start_pattern = r"tradingContents\.forEach\(c => c\.classList\.add\('hidden'\)\);"
end_pattern = r"const perChangeColor = item\.PerChange > 0 \? 'var\(--up-color\)' : item\.PerChange < 0 \? 'var\(--down-color\)' : 'var\(--ref-color\)';"

replacement = """tradingContents.forEach(c => c.classList.add('hidden'));
            
            tab.classList.add('active');
            tab.style.background = '#8b5cf6';
            tab.style.color = 'white';
            tab.style.border = 'none';
            
            const target = document.getElementById(tab.getAttribute('data-target'));
            if (target) {
                target.classList.remove('hidden');
            }
            
            if (currentTicker) {
                renderTrading(currentTicker);
            }
        });
    });

    async function fetchTradingData(ticker, fromDate, toDate) {
        if (!tradingTbody) return;
        
        try {
            const url = `http://localhost:8080/api/v3/market_data/market_watch/price_history/${ticker}?from_date=${fromDate}&to_date=${toDate}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('API Error');
            const json = await res.json();
            
            if (!json.success || !json.response || json.response.length === 0) {
                tradingTbody.innerHTML = '<tr><td colspan="13" style="text-align:center; padding: 20px;">Không có dữ liệu trong khoảng thời gian này</td></tr>';
                return;
            }
            
            let html = '';
            json.response.forEach(item => {
                const dateParts = item.TradingDate.split('-');
                const formattedDate = dateParts.length === 3 ? `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}` : item.TradingDate;
                
                const perChangeColor = item.PerChange > 0 ? 'var(--up-color)' : item.PerChange < 0 ? 'var(--down-color)' : 'var(--ref-color)';"""

new_content = re.sub(f'{start_pattern}.*?{end_pattern}', replacement, content, flags=re.DOTALL)

with open('dashboard/js/app.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Fixed app.js successfully')
