import os
import pandas as pd
import logging

from config import LONG, SHORT

from .ReportingUtils import get_statistical_summary_of_trades
from .ReportingUtils import plot_the_budget_vs_time
from .ReportingUtils import draw_trades_executions
from .ReportingUtils import plot_duration_of_net_exposure
from .ReportingUtils import plot_histogram
from .ReportingUtils import plot_qq

from src.TradingTools import get_net_exposure

simulation_logger = logging.getLogger("simulation_logger")


def generate_report_for_trades_history(
    trades_df, daily_budget_dfs, stock_histories, **params
):
    """
    ## GUIDE: Step 9

    Generate the report for the trades history

    This function generates the report for the trades history.


    Args:
        trades_df: pd.DataFrame
            The trades history

        daily_budget_dfs: pd.DataFrame
            The daily budget dataframes

        stock_histories: AllStocksPrices
            The stock histories

        params: dict
            The parameters for the simulation

    Returns:
        summaries_df: pd.DataFrame
    """

    enums = params["enums"]
    # Converting to datetime
    df = trades_df
    df_g = daily_budget_dfs

    df_g["net_exposure"] = get_net_exposure(
        df_g["long_positions_values"], df_g["short_positions_values"]
    )

    should_log = params.get("should_log")

    # Save the plots and executed trades
    if should_log:
        market_index = stock_histories.market_index
        df = trades_df

        df.to_csv(os.path.join(enums.TRADE_REPORTS_DIR, "ExecutedTrades.csv"))

        plot_the_budget_vs_time(df_g, market_index, enums.TRADE_REPORTS_DIR, **params)
        _generate_report_for_symbols(df, enums.TRADE_REPORTS_DIR, **params)

        try:
            df_g = pd.merge(
                df_g,
                stock_histories.market_index["Close"],
                left_index=True,
                right_index=True,
                how="left",
            )
            df_g.rename(columns={"Close": "MarketIndexClose"}, inplace=True)
        except Exception as e:
            pass

        df_g.to_csv(os.path.join(enums.TRADE_REPORTS_DIR, "DailyBudget.csv"))

    # Finding the statistical summaries of the whole df
    summaries_df = get_statistical_summary_of_trades(trades_df, df_g, **params)

    if should_log:
        market, strategy_name = params["market"], params["strategy_name"]
        summaries_df.to_csv(
            f"reports/{market}/{strategy_name}/Summary_{strategy_name}.csv"
        )
        simulation_logger.info(
            "\n----------------------------------------------------------\n"
            + summaries_df.to_string()
            + "\n----------------------------------------------------------\n"
        )

    if should_log:
        draw_trades_executions(stock_histories, **params)
        plot_duration_of_net_exposure(df_g, **params)
        plot_histogram(df_g, **params)
        plot_qq(df_g, **params)
        ## TODO: ASSIGNMENT #1

    return summaries_df


def _generate_report_for_symbols(df, TRADE_REPORTS_DIR, **params):

    holder = []
    for symbol in set(df["symbol"].values):

        df_tmp = df[df["symbol"] == symbol]

        df_tmp_long = df_tmp[df_tmp["trade_direction"] == LONG]
        df_tmp_short = df_tmp[df_tmp["trade_direction"] == SHORT]
        holder.append(
            {
                "Symbol": symbol,
                "Count": len(df_tmp),
                "Count_Long": len(df_tmp_long),
                "Count_Short": len(df_tmp_short),
                "win": df_tmp["is_successful"].mean(),
                "win_long": df_tmp_long["is_successful"].mean(),
                "win_short": df_tmp_short["is_successful"].mean(),
                "PnL_ratio_mean": df_tmp["PnL_ratio"].mean(),
                "PnL_ratio_long_mean": df_tmp_long["PnL_ratio"].mean(),
                "PnL_ratio_short_mean": df_tmp_short["PnL_ratio"].mean(),
            }
        )

    df_to_save = pd.DataFrame(holder)
    df_to_save.to_csv(os.path.join(TRADE_REPORTS_DIR, "SummaryOfExecutedTradesIn.csv"))

    return
