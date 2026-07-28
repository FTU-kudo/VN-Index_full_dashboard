# FILE: scripts/inspect_response.py
from __future__ import annotations
import click
import json
from src.data.yuanta_client import yuanta_client

@click.group()
def cli():
    """Development tool to inspect raw Yuanta API responses."""
    pass

@cli.command()
def sector():
    """List 18 sectors and number of stocks in each sector."""
    endpoint = "market_data/price_board/stock/list_stock_by_sector"
    response = yuanta_client.get(endpoint)
    
    if response and isinstance(response, dict) and response.get("success"):
        sectors = response.get("response", [])
        click.echo(f"Found {len(sectors)} sectors:")
        for sec in sectors:
            sector_name = sec.get("Sector", "N/A")
            stocks = sec.get("Stocks", [])
            click.echo(f"- {sector_name}: {len(stocks)} stocks")
    else:
        click.echo("Failed to fetch sector data.", err=True)

@cli.command()
@click.option('--exchange', type=click.Choice(['HSX', 'HNX', 'UPCOM']), required=True, help="Stock exchange")
def universe(exchange: str):
    """Get statistics of the stock universe for a specific exchange."""
    endpoint = "market_data/price_board/stock/list_stock_info"
    params = {"exchange": exchange}
    response = yuanta_client.get(endpoint, params=params)
    
    if response and isinstance(response, dict) and response.get("success"):
        stocks = response.get("response", [])
        click.echo(f"Exchange {exchange} has {len(stocks)} stocks.")
        if stocks:
            click.echo(f"Sample data for {stocks[0].get('StockCode')}:")
            click.echo(json.dumps(stocks[0], indent=2))
    else:
        click.echo(f"Failed to fetch universe for {exchange}.", err=True)

if __name__ == '__main__':
    cli()
