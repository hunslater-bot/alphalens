#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from unittest import TestCase
from nose_parameterized import parameterized
from numpy import nan
from pandas import (
    Series,
    DataFrame,
    date_range,
    MultiIndex,
    Int64Index,
    Index,
    DatetimeIndex,
    Timedelta
)

from pandas.util.testing import (assert_frame_equal,
                                 assert_series_equal)

from .. performance import (factor_information_coefficient,
                            mean_information_coefficient,
                            quantile_turnover,
                            factor_rank_autocorrelation,
                            factor_returns, factor_alpha_beta,
                            cumulative_returns,
                            average_cumulative_return_by_quantile)

from .. utils import (get_forward_returns_columns,
                      get_clean_factor_and_forward_returns)


class PerformanceTestCase(TestCase):
    dr = date_range(start='2015-1-1', end='2015-1-2')
    dr.name = 'date'
    tickers = ['A', 'B', 'C', 'D']
    factor = DataFrame(index=dr,
                       columns=tickers,
                       data=[[1, 2, 3, 4],
                             [4, 3, 2, 1]]).stack()
    factor.index = factor.index.set_names(['date', 'asset'])
    factor.name = 'factor'
    factor_data = DataFrame()
    factor_data['factor'] = factor
    factor_data['group'] = Series(index=factor.index,
                                  data=[1, 1, 2, 2, 1, 1, 2, 2],
                                  dtype="category")

    @parameterized.expand([(factor_data, [4, 3, 2, 1, 1, 2, 3, 4],
                            False, False,
                            dr,
                            [-1., -1.],
                            ),
                           (factor_data, [1, 2, 3, 4, 4, 3, 2, 1],
                            False, False,
                            dr,
                            [1., 1.],
                            ),
                           (factor_data, [1, 2, 3, 4, 4, 3, 2, 1],
                            False, True,
                            MultiIndex.from_product(
                                [dr, [1, 2]], names=['date', 'group']),
                            [1., 1., 1., 1.],
                            ),
                           (factor_data, [1, 2, 3, 4, 4, 3, 2, 1],
                            True, True,
                            MultiIndex.from_product(
                                [dr, [1, 2]], names=['date', 'group']),
                            [1., 1., 1., 1.],
                            )])
    def test_information_coefficient(self,
                                     factor_data,
                                     forward_returns,
                                     group_adjust,
                                     by_group,
                                     expected_ix,
                                     expected_ic_val):

        factor_data['1D'] = Series(index=factor_data.index,
                                   data=forward_returns)

        ic = factor_information_coefficient(factor_data=factor_data,
                                            group_adjust=group_adjust,
                                            by_group=by_group)

        expected_ic_df = DataFrame(index=expected_ix,
                                   columns=Index(['1D'], dtype='object'),
                                   data=expected_ic_val)

        assert_frame_equal(ic, expected_ic_df)

    @parameterized.expand([(factor_data,
                            [4, 3, 2, 1, 1, 2, 3, 4],
                            False,
                            False,
                            'D',
                            dr,
                            [-1., -1.]),
                           (factor_data,
                            [1, 2, 3, 4, 4, 3, 2, 1],
                            False,
                            False,
                            'W',
                            DatetimeIndex(['2015-01-04'],
                                          name='date',
                                          freq='W-SUN'),
                            [1.]),
                           (factor_data,
                            [1, 2, 3, 4, 4, 3, 2, 1],
                            False,
                            True,
                            None,
                            Int64Index([1, 2], name='group'),
                            [1., 1.]),
                           (factor_data,
                            [1, 2, 3, 4, 4, 3, 2, 1],
                            False,
                            True,
                            'W',
                            MultiIndex.from_product(
                                [DatetimeIndex(['2015-01-04'],
                                               name='date',
                                               freq='W-SUN'),
                                 [1, 2]], names=['date', 'group']),
                            [1., 1.])])
    def test_mean_information_coefficient(self,
                                          factor_data,
                                          forward_returns,
                                          group_adjust,
                                          by_group,
                                          by_time,
                                          expected_ix,
                                          expected_ic_val):

        factor_data['1D'] = Series(index=factor_data.index,
                                   data=forward_returns)

        ic = mean_information_coefficient(factor_data,
                                          group_adjust=group_adjust,
                                          by_group=by_group,
                                          by_time=by_time)

        expected_ic_df = DataFrame(index=expected_ix,
                                   columns=Index(['1D'], dtype='object'),
                                   data=expected_ic_val)

        assert_frame_equal(ic, expected_ic_df)

    @parameterized.expand([([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 4.0, '1D',
                            [nan, 1.0, 1.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 4.0, '1D',
                            [nan, 1.0, 1.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '10T', 4.0, '10min',
                            [nan, 1.0, 1.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 4.0, '2D',
                            [nan, nan, 0.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 4.0, '2D',
                            [nan, nan, 0.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1H', 4.0, '2H',
                            [nan, nan, 0.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 4.0, '3D',
                            [nan, nan, nan, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 4.0, '3D',
                            [nan, nan, nan, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1H', 4.0, '3H',
                            [nan, nan, nan, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 3.0, '1D',
                            [nan, 0.0, 0.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 3.0, '1D',
                            [nan, 0.0, 0.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 3.0, '2D',
                            [nan, nan, 0.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 3.0, '2D',
                            [nan, nan, 0.0, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 3.0, '3D',
                            [nan, nan, nan, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 3.0, '3D',
                            [nan, nan, nan, 0.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0]],
                            '1B', 2.0, '1D',
                            [nan, 1.0, 1.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0]],
                            '1D', 2.0, '1D',
                            [nan, 1.0, 1.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0]],
                            '1B', 3.0, '4D',
                            [nan, nan, nan, nan,
                             0., 0., 0., 0.,
                             0., 0., 0., 0.]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0]],
                            '1D', 3.0, '4D',
                            [nan, nan, nan, nan,
                             0., 0., 0., 0.,
                             0., 0., 0., 0.]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', 3.0, '10D',
                            [nan, nan, nan, nan, nan,
                             nan, nan, nan, nan, nan,
                             0., 1.]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 3.0, 2.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', 3.0, '10D',
                            [nan, nan, nan, nan, nan,
                             nan, nan, nan, nan, nan,
                             0., 1.])
                           ])
    def test_quantile_turnover(self, quantile_values, freq, test_quantile,
                               period, expected_vals):

        dr = date_range(start='2015-1-1', periods=len(quantile_values),
                        freq=freq)
        dr.name = 'date'
        tickers = ['A', 'B', 'C', 'D']

        quantized_test_factor = Series(DataFrame(index=dr,
                                                 columns=tickers,
                                                 data=quantile_values)
                                       .stack())
        quantized_test_factor.index = quantized_test_factor.index.set_names(
            ['date', 'asset'])

        to = quantile_turnover(quantized_test_factor, test_quantile, period)

        expected = Series(
            index=quantized_test_factor.index.levels[0], data=expected_vals)
        expected.name = test_quantile

        assert_series_equal(to, expected)

    @parameterized.expand([([1, 2, 3, 4, 4, 3, 2, 1],
                            [4, 3, 2, 1, 1, 2, 3, 4],
                            False,
                            [-1.25000, -1.25000]),
                           ([1, 1, 1, 1, 1, 1, 1, 1],
                            [4, 3, 2, 1, 1, 2, 3, 4],
                            False,
                            [nan, nan]),
                           ([1, 2, 3, 4, 4, 3, 2, 1],
                            [4, 3, 2, 1, 1, 2, 3, 4],
                            True,
                            [-0.5, -0.5]),
                           ([1, 2, 3, 4, 1, 2, 3, 4],
                            [1, 4, 1, 2, 1, 2, 2, 1],
                            True,
                            [1.0, 0.0]),
                           ([1, 1, 1, 1, 1, 1, 1, 1],
                            [4, 3, 2, 1, 1, 2, 3, 4],
                            True,
                            [nan, nan])
                           ])
    def test_factor_returns(self,
                            factor_vals,
                            fwd_return_vals,
                            group_adjust,
                            expected_vals):

        factor_data = self.factor_data.copy()
        factor_data['1D'] = fwd_return_vals
        factor_data['factor'] = factor_vals

        factor_returns_s = factor_returns(factor_data=factor_data,
                                          demeaned=True,
                                          group_adjust=group_adjust)

        expected = DataFrame(
            index=self.dr,
            data=expected_vals,
            columns=get_forward_returns_columns(
                factor_data.columns))

        assert_frame_equal(factor_returns_s, expected)

    @parameterized.expand([([1, 2, 3, 4, 1, 1, 1, 1],
                            -1,
                            5. / 6.)])
    def test_factor_alpha_beta(self, fwd_return_vals, alpha, beta):

        factor_data = self.factor_data.copy()
        factor_data['1D'] = fwd_return_vals

        ab = factor_alpha_beta(factor_data=factor_data)

        expected = DataFrame(columns=['1D'],
                             index=['Ann. alpha', 'beta'],
                             data=[alpha, beta])

        assert_frame_equal(ab, expected)

    @parameterized.expand([([1.0, 0.5, 1.0, 0.5, 0.5],
                            '1D', '1D',
                            [1.0, 2.0, 3.0, 6.0, 9.0, 13.50]),
                           ([1.0, 0.5, 1.0, 0.5, 0.5],
                            '1D', '45m',
                            [1., 2., 2., 3., 3.0, 6.0, 6.0, 9.0, 9.0, 13.50]),
                           ([0.1, 0.1, 0.1, 0.1, 0.1],
                            '1D', '1D',
                            [1.0, 1.1, 1.21, 1.331, 1.4641, 1.61051]),
                           ([-0.1, -0.1, -0.1, -0.1, -0.1],
                            '1D', '1D',
                            [1.0, 0.9, 0.81, 0.729, 0.6561, 0.59049]),
                           ([1.0, 0.5, 1.0, 0.5, 0.5],
                            '1B', '1D',
                            [1.0, 2.0, 3.0, 6.0, 9.0, 13.50]),
                           ([1.0, 0.5, 1.0, 0.5, 0.5],
                            '1B', '45m',
                            [1., 2., 2., 3., 3.0, 6.0, 6.0, 9.0, 9.0, 13.50]),
                           ([0.1, 0.1, 0.1, 0.1, 0.1],
                            '1B', '1D',
                            [1.0, 1.1, 1.21, 1.331, 1.4641, 1.61051]),
                           ([-0.1, -0.1, -0.1, -0.1, -0.1],
                            '1B', '1D',
                            [1.0, 0.9, 0.81, 0.729, 0.6561, 0.59049]),
                           ([1.0, nan, 0.5, nan, 1.0, nan, 0.5, nan, 0.5],
                            '20S', '20s',
                            [1.0, 2., 2., 3., 3.0, 6.0, 6.0, 9.0, 9.0, 13.50]),
                           ([0.1, 0, 0.1, 0, 0.1, 0, 0.1, 0, 0.1],
                            '10T', '10m',
                            [1.0, 1.1, 1.1, 1.21, 1.21, 1.331, 1.331, 1.4641,
                             1.4641, 1.61051]),
                           ([3.0, 0.0, 0.0],
                            '1H', '2h',
                            [1.0, 2.0, 3.0, 3.0, 3.0]),
                           ([1.0, 1.0, 1.0, 1.0, 1.0],
                            '1H', '2h',
                            [1.0, 1.4142, 2.0, 2.8284, 4.0, 5.6568, 8.0]),
                           ([0.1, 0.1, 0.1, 0.1, 0.1],
                            '1H', '2h',
                            [1.0, 1.0488, 1.1, 1.15368, 1.21, 1.26905, 1.331]),
                           ([-0.1, -0.1, -0.1, -0.1, -0.1],
                            '1T', '2m',
                            [1.0, 0.94868, 0.9, 0.8538, 0.81, 0.76843, 0.729]),
                           ([-0.75, -0.75, -0.75, -0.75, -0.75],
                            '1D', '2D',
                            [1., 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]),
                           ([3.0, 3.0, 3.0, 3.0, 3.0],
                            '1D', '2D',
                            [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]),
                           ([3.0, -0.75, 3.0, -0.75, 3.0],
                            '1h', '2h',
                            [1.0, 2.0, 2.5, 3.125, 3.90625, 4.88281, 9.76562]),
                           ([3.0, -0.75],
                            '1D', '2D',
                            [1.0, 2.0, 2.5, 1.25]),
                           ([7.0, -0.875, 7.0, -0.875, 7.0],
                            '1D', '3D',
                            [1.0, 2.0, 2.5, 3.75, 3.75, 5.625, 7.03125,
                             14.0625]),
                           ([7.0, -0.875, nan, 7.0, -0.875],
                            '1D', '3D',
                            [1.0, 2.0, 2.5, 3.125, 3.90625, 4.88281, 6.10351,
                             3.05175]),
                           ([7.0, nan, nan, -0.875, 7.0, nan, nan, nan, 7.0,
                             nan, -0.875],
                            '1h', '3h',
                            [1.0, 2.0, 4.0, 8.0, 4.0, 5.0, 6.25, 12.5, 12.5,
                             25., 50., 62.5, 31.25, 15.625]),
                           ([15., nan, nan, -0.9375, 15., nan, nan, nan, 15.],
                            '1D', '4D',
                            [1.0, 2.0, 4.0, 8.0, 10.0, 12.5, 15.625, 19.53125,
                             39.0625, 78.125, 156.25, 312.5, 625.0]),
                           ([15.0, -0.9375, 15.0, -0.9375],
                            '1D', '4D',
                            [1.0, 2.0, 2.5, 3.75, 4.6875, 4.6875, 5.85937,
                             2.92968]),
                           ])
    def test_cumulative_returns(self, returns, ret_freq, period_len,
                                expected_vals):

        period_len = Timedelta(period_len)
        index = date_range('1/1/1999', periods=len(returns), freq=ret_freq)
        returns = Series(returns, index=index)

        cum_ret = cumulative_returns(returns, period_len)

        expected = Series(expected_vals, index=cum_ret.index)

        assert_series_equal(cum_ret, expected, check_less_precise=True)

    @parameterized.expand([([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', '1D',
                            [nan, 1.0, 1.0, 1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', '1D',
                            [nan, 1.0, 1.0, 1.0]),
                           ([[4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1B', '1D',
                            [nan, -1.0, -1.0, -1.0]),
                           ([[4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0]],
                            '1D', '1D',
                            [nan, -1.0, -1.0, -1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0]],
                            '1B', '3D',
                            [nan, nan, nan, 1.0, 1.0,
                             1.0, 0.6, -0.6, -1.0, 1.0,
                             -0.6, -1.0]),
                           ([[1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0],
                             [1.0, 2.0, 3.0, 4.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [2.0, 1.0, 4.0, 3.0],
                             [4.0, 3.0, 2.0, 1.0]],
                            '1D', '3D',
                            [nan, nan, nan, 1.0, 1.0,
                             1.0, 0.6, -0.6, -1.0, 1.0,
                             -0.6, -1.0])
                           ])
    def test_factor_rank_autocorrelation(self,
                                         factor_values,
                                         freq,
                                         period,
                                         expected_vals):

        dr = date_range(start='2015-1-1', periods=len(factor_values),
                        freq=freq)
        dr.name = 'date'
        tickers = ['A', 'B', 'C', 'D']
        factor = DataFrame(index=dr,
                           columns=tickers,
                           data=factor_values).stack()
        factor.index = factor.index.set_names(['date', 'asset'])

        factor_df = DataFrame()
        factor_df['factor'] = factor

        fa = factor_rank_autocorrelation(factor_df, period)
        expected = Series(index=dr, data=expected_vals)
        expected.name = period

        assert_series_equal(fa, expected)

    @parameterized.expand([(1, 2, False, 4,
                            [[1.00, 0.0, -0.50, -0.75],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.00, 0.00, 0.00, 0.00],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.20, 0.0, 0.25, 0.5625],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.3333333, 0.0, 0.50, 1.25],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (1, 2, True, 4,
                            [[0.8833333, 0.0, -0.5625, -1.015625],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.1166667, 0.0, -0.0625, -0.265625],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.3166667, 0.0, 0.1875, 0.296875],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.4500000, 0.0, 0.4375, 0.984375],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (3, 0, False, 4,
                            [[7.0, 3.0, 1.0, 0.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.488, -0.36, -0.2, 0.0],
                             [0.0, 0.0, 0.0, 0.0],
                             [-0.703704, -0.55555555, -0.333333333, 0.0],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (0, 3, True, 4,
                            [[0.0, -0.5625, -1.015625, -1.488281],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, -0.0625, -0.265625, -0.613281],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.1875, 0.296875, 0.339844],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.4375, 0.984375, 1.761719],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (3, 3, False, 2,
                            [[3.5, 1.5, 0.5, 0.0, -0.25, -0.375, -0.4375],
                             [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                             [-0.595852, -0.457778, -0.266667, 0.0, 0.375,
                              0.90625, 1.664062],
                             [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]),
                           (3, 3, True, 2,
                            [[2.047926, 0.978888, 0.383333, 0.0, -0.3125,
                              -0.640625, -1.050781],
                             [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                             [-2.047926, -0.978888, -0.383333, 0.0, 0.3125,
                              0.640625, 1.050781],
                             [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]),
                           ])
    def test_average_cumulative_return_by_quantile(self, before, after,
                                                   demeaned, quantiles,
                                                   expected_vals):
        dr = date_range(start='2015-1-15', end='2015-2-1')
        dr.name = 'date'
        tickers = ['A', 'B', 'C', 'D']
        r1, r2, r3, r4 = (1.25, 1.50, 1.00, 0.50)
        data = [[r1**i, r2**i, r3**i, r4**i] for i in range(1, 19)]
        prices = DataFrame(index=dr, columns=tickers, data=data)
        dr2 = date_range(start='2015-1-21', end='2015-1-26')
        dr2.name = 'date'
        factor = DataFrame(
            index=dr2, columns=tickers, data=[
                [3, 4, 2, 1],
                [3, 4, 2, 1],
                [3, 4, 2, 1],
                [3, 4, 2, 1],
                [3, 4, 2, 1],
                [3, 4, 2, 1]]).stack()

        factor_data = get_clean_factor_and_forward_returns(
            factor, prices, quantiles=quantiles, periods=range(
                0, after + 1), filter_zscore=False)

        avgrt = average_cumulative_return_by_quantile(
            factor_data, prices, before, after, demeaned)
        arrays = []
        for q in range(1, quantiles + 1):
            arrays.append((q, 'mean'))
            arrays.append((q, 'std'))
        index = MultiIndex.from_tuples(arrays, names=['factor_quantile', None])
        expected = DataFrame(
            index=index, columns=range(-before, after + 1), data=expected_vals)
        assert_frame_equal(avgrt, expected)

    @parameterized.expand([(0, 2, False, 4,
                            [[0.0, -0.50, -0.75],
                             [0.0, 0.0, 0.0],
                             [0.0, 0.0, 0.0],
                             [0.0, 0.0, 0.0],
                             [0.0, 0.25, 0.5625],
                             [0.0, 0.0, 0.0],
                             [0.0, 0.50, 1.25],
                             [0.0, 0.0, 0.0]]),
                           (0, 3, True, 4,
                            [[0.0, -0.5625, -1.015625, -1.488281],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, -0.0625, -0.265625, -0.613281],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.1875, 0.296875, 0.339844],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.4375, 0.984375, 1.761719],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (0, 3, False, 2,
                            [[0.0, -0.25, -0.375, -0.4375],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.375, 0.90625, 1.664062],
                             [0.0, 0.0, 0.0, 0.0]]),
                           (0, 3, True, 2,
                            [[0.0, -0.3125, -0.640625, -1.050781],
                             [0.0, 0.0, 0.0, 0.0],
                             [0.0, 0.3125, 0.640625, 1.050781],
                             [0.0, 0.0, 0.0, 0.0]]),
                           ])
    def test_average_cumulative_return_by_quantile_2(self, before, after,
                                                     demeaned, quantiles,
                                                     expected_vals):
        """
        Test varying factor asset universe: at different dates there might be
        different assets
        """
        dr = date_range(start='2015-1-15', end='2015-1-25')
        dr.name = 'date'
        tickers = ['A', 'B', 'C', 'D', 'E', 'F']
        r1, r2, r3, r4 = (1.25, 1.50, 1.00, 0.50)
        data = [[r1**i, r2**i, r3**i, r4**i, r2**i, r3**i]
                for i in range(1, 12)]
        prices = DataFrame(index=dr, columns=tickers, data=data)
        dr2 = date_range(start='2015-1-18', end='2015-1-21')
        dr2.name = 'date'
        factor = DataFrame(index=dr2, columns=tickers,
                           data=[[3, 4, 2, 1, nan, nan],
                                 [3, 4, 2, 1, nan, nan],
                                 [3, nan, nan, 1, 4, 2],
                                 [3, nan, nan, 1, 4, 2]]).stack()

        factor_data = get_clean_factor_and_forward_returns(
            factor, prices, quantiles=quantiles, periods=range(
                0, after + 1), filter_zscore=False)

        avgrt = average_cumulative_return_by_quantile(
            factor_data, prices, before, after, demeaned)
        arrays = []
        for q in range(1, quantiles + 1):
            arrays.append((q, 'mean'))
            arrays.append((q, 'std'))
        index = MultiIndex.from_tuples(arrays, names=['factor_quantile', None])
        expected = DataFrame(
            index=index, columns=range(-before, after + 1), data=expected_vals)
        assert_frame_equal(avgrt, expected)
