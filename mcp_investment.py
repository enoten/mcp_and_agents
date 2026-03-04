import math

from fastmcp import FastMCP
import numpy_financial as npf

# Initialize the FastMCP server with a descriptive name
mcp = FastMCP("FinanceTools")

@mcp.tool()
def calculate_npv(
    discount_rate: float, 
    cash_flows: list[float], 
    initial_investment: float = 0.0
) -> float:
    """
    Calculate the Net Present Value (NPV) of a series of future cash flows.
    
    Args:
        discount_rate: The required rate of return or discount rate per period 
                       (entered as a decimal, e.g., 0.05 for 5%).
        cash_flows: A list of expected cash inflows/outflows for each period, 
                    starting from period 1.
        initial_investment: The initial cash outflow at period 0. 
                            (Enter as a positive number; it will be subtracted).
                            
    Returns:
        The calculated Net Present Value as a float.
    """
    # Start by subtracting the initial investment at time t=0
    npv = -initial_investment
    
    # Calculate the present value for each subsequent cash flow
    for t, cash_flow in enumerate(cash_flows, start=1):
        npv += cash_flow / ((1 + discount_rate) ** t)
        
    return round(npv, 4)

@mcp.tool()
def calculate_irr(
    cash_flows: list[float], 
    initial_investment: float = 0.0
) -> float:
    """
    Calculate the Internal Rate of Return (IRR) for a series of cash flows.
    
    Args:
        cash_flows: A list of expected cash inflows/outflows for each period.
        initial_investment: The initial cash outflow at period 0 (positive number).
        
    Returns:
        The Internal Rate of Return as a decimal (e.g., 0.15 means 15%). 
        Returns 0.0 if a valid IRR cannot be found.
    """
    # Combine initial investment (as an outflow) with future cash flows
    all_cash_flows = [-initial_investment] + cash_flows
    
    # Calculate IRR
    irr = npf.irr(all_cash_flows)
    
    # Handle edge cases where IRR cannot be calculated
    if irr is None or math.isnan(irr):
        return 0.0
        
    return round(float(irr), 4)

@mcp.tool()
def calculate_payback_period(
    cash_flows: list[float], 
    initial_investment: float
) -> float:
    """
    Calculate the Payback Period for an investment.
    
    Args:
        cash_flows: A list of expected cash inflows for each period (starting period 1).
        initial_investment: The initial cash outflow at period 0 (positive number).
        
    Returns:
        The payback period in terms of periods/years as a float. 
        Returns -1.0 if the investment is never fully recovered within the provided cash flows.
    """
    unrecovered_cost = initial_investment
    
    for t, cash_flow in enumerate(cash_flows, start=1):
        # If the cash flow is negative or zero, it just adds to (or doesn't help) the unrecovered cost
        if cash_flow <= 0:
            unrecovered_cost -= cash_flow 
            continue
            
        # If this period's cash flow is enough to cover the remaining cost
        if unrecovered_cost <= cash_flow:
            fraction_of_period = unrecovered_cost / cash_flow
            return round((t - 1) + fraction_of_period, 4)
        
        # Otherwise, deduct the cash flow and move to the next period
        unrecovered_cost -= cash_flow
        
    # If the loop finishes without recovering the full investment
    return -1.0

if __name__ == "__main__":
    # Run the server using standard input/output (the default for MCP)
    mcp.run(transport="http",
            host="0.0.0.0",
            port=8004)