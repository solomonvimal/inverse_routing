#!/usr/local/anaconda/bin/python

''' This scripts reads in direct output file from the inverse routing, and convert the result to VIC output format, which is in the format of Lohmann routing model input '''

import numpy as np
import datetime as dt
import os
import argparse
import my_functions

parser = argparse.ArgumentParser()
parser.add_argument("--cfg", type=str,  help="config file for this script")
args = parser.parse_args()
cfg = my_functions.read_config(args.cfg)

start_date = dt.datetime(cfg['PARAM']['start_date'][0], \
                         cfg['PARAM']['start_date'][1], \
                         cfg['PARAM']['start_date'][2])

#===============================================================#
# Read in inverse routing output
#===============================================================#
# A dictionary; keys: 'lat_lon'; element: Series of total runoff
dict_s_total_runoff = my_functions.read_inverse_route_output(\
                                       cfg['INPUT']['inv_ro_basin_output_dir'], \
                                       smooth_window=cfg['PARAM']['smooth_window'], \
                                       skip_steps=cfg['PARAM']['skip_steps'], \
                                       start_date=start_date, \
                                       time_step=cfg['PARAM']['time_step'], \
                                       latlon_precision=cfg['PARAM']['latlon_precision'])

#===============================================================#
# Write into VIC output format, convert to daily data if not already
# (Lohmann routing input format)
# Format: YYYY MM DD SKIP SKIP RUNOFF BASEFLOW
#   (Here, SKIP is set to -99, RUNOFF is set to total runoff, BASEFLOW is set to 0)
# These output files are for VIC calibration and routing purpose
#===============================================================#
#for lat_lon in dict_s_total_runoff.keys():
#    print 'Writing grid cell {}...'.format(lat_lon)
#    filename = '{}/{}_{}'.format(cfg['OUTPUT']['output_VIC_runoff_dir'], \
#                                 cfg['OUTPUT']['output_VIC_prefix'], \
#                                 lat_lon)
#    # Convert to daily data if not already
#    if cfg['PARAM']['time_step']!=24:
#        print 'Currently do not support non-daily data!'
#        exit()
#    else:
#        s_total_runoff = dict_s_total_runoff[lat_lon]
#    # Write data to file
#    f = open(filename, 'w')
#    for i in range(len(s_total_runoff)):
#        f.write('{:4d} {:02d} {:02d} -99 -99 {:f} 0\n'\
#                    .format(s_total_runoff.index[i].year, s_total_runoff.index[i].month, \
#                            s_total_runoff.index[i].day, s_total_runoff[i]))
#    f.close()

#===============================================================#
# Calculate stats for runoff
#===============================================================#
start_date_WY, end_date_WY = my_functions.find_full_water_years_within_a_range(\
                                dict_s_total_runoff[dict_s_total_runoff.keys()[0]].index[0],\
                                dict_s_total_runoff[dict_s_total_runoff.keys()[0]].index[-1])
for lat_lon in dict_s_total_runoff.keys():
    print 'Calculating stats for grid cell {}...'.format(lat_lon)
    s_total_runoff = dict_s_total_runoff[lat_lon]
    #--- Select full water year ---#
    s_total_runoff = my_functions.select_time_range(s_total_runoff, \
                                                    start_date_WY, \
                                                    end_date_WY)

    #--- Calculate monthly data and write to file ---#
    # Calculate
    s_monthly = my_functions.calc_monthly_data(s_total_runoff)
    # Create subdirectories
    dir_monthly = '{}/monthly'.format(cfg['OUTPUT']['output_stats_basedir'])
    if not os.path.exists(dir_monthly):
        os.makedirs(dir_monthly)
    # Write output (format: <year> <month> <runoff, mm/day>)
    filename = '{}/{}_monthly_{}'.format(dir_monthly, \
                                         cfg['OUTPUT']['output_VIC_prefix'], \
                                         lat_lon)
    f = open(filename, 'w')
    f.write('Year Month Total_runoff_mm_day\n')
    for i in range(len(s_monthly)):
        f.write('{:4d} {:02d} {:f}\n'\
                    .format(s_monthly.index[i].year, s_monthly.index[i].month, \
                            s_monthly[i]))
    f.close()

    #--- Calculate seasonality data and write to file ---#
    # Calculate
    s_seas = my_functions.calc_ts_stats_by_group(s_total_runoff, \
                                                 'month', 'mean') # ndex is 1-12 (month)
    # Create subdirectories
    dir_seas = '{}/seasonality_WY{}_{}'.format(cfg['OUTPUT']['output_stats_basedir'], \
                                                  start_date_WY.year+1, \
                                                  end_date_WY.year)
    if not os.path.exists(dir_seas):
        os.makedirs(dir_seas)
    # Write output (format: <month> <runoff, mm/day>)
    filename = '{}/{}_seas_{}'.format(dir_seas, \
                                         cfg['OUTPUT']['output_VIC_prefix'], \
                                         lat_lon)
    s_seas.to_csv(filename, sep=' ', header=['Total_runoff_mm_day'], \
                  index=True, index_label='Month')
    
    







