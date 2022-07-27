import streamlit as st
from fake_useragent import UserAgent
import requests
import pandas as pd
#import json



ua = UserAgent()
header = {'User-Agent': str(ua.chrome)}
state_response = requests.get(f"https://cdn-api.co-vin.in/api/v2/admin/location/states",headers=header)
state_response.raise_for_status() 
if state_response.status_code != 204:
    state = state_response.json()
states_dict = {}
states_dict['0'] = ' '
for i in states['states']:
    states_dict[i['state_id']] = i['state_name']
states_list = list(states_dict.values())


def get_key(dict,val):
    for key, value in dict.items():
        if val == value:
            return key
    return "key doesn't exist"

def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    file = df.to_csv(index=False, encoding='UTF-8')
    href = f'<a href="data:file/csv;{file}" download="{filename}">{text}</a>'
    return href

def get_districts(key):
    district_response = requests.get(f"https://cdn-api.co-vin.in/api/v2/admin/location/districts/{key}", headers=header)
    district_response.raise_for_status() 
    if district_response.status_code != 204:
        district = district_response.json()
    district_dict = {}
    district_dict['0'] = ' '
    for i in district['districts']:
        district_dict[i['district_id']] = i['district_name']
    return district_dict

def run():
    
    st.sidebar.markdown("<h1 style='text-align: center;'>Covid-19 Vaccine Tracker</h>", unsafe_allow_html=True)
    st.sidebar.image('logo1.png')
    st.markdown("### Check Available Vaccination Slots!")
    choice = st.sidebar.radio(
        'Select an Option',
        ('Search by Pin','Search by District')
    )


    if choice == 'Search by District':
        states_list.remove('Daman and Diu')
        states_box = st.sidebar.selectbox("Select State",states_list)
        
        state_index = states_list.index(states_box)

        district_dict = get_districts(state_index)
        district_list = list(district_dict.values())

        ## Select Districts
        district_list.insert(0,' ')
        district_box = st.sidebar.selectbox("Select District", district_list)
            
        dist_key = get_key(district_dict,district_box)

        col1, col2 = st.columns(2)
        with col1:
            ## Age
            age_display = ['18 & Above', '18-45', '45+']
            age = st.selectbox("Your Age", age_display)
            age_val = 0

            ## Select Date
            vac_date = st.date_input("Date")
            vac_date = str(vac_date).split('-')
            new_date = vac_date[2] + '-' + vac_date[1] + '-' + vac_date[0]

        with col2:
            ## Vaccine Type
            vacc_display = ['Covishield','Covaxin', 'Sputnik V']
            vaccine = st.selectbox("Vaccine Type", vacc_display)
            vaccine_type = ''
            if vaccine == 'Covishield':
                vaccine_type = 'COVISHIELD'
            elif vaccine == 'Covaxin':
                vaccine_type = 'COVAXIN'
            else:
                vaccine_type = 'SPUTNIK V'

            ## Fee Type
            fee_display = ['Free','Paid']
            fee = st.selectbox("Fee Type", fee_display)

        

        if st.button("Search"):
            # Fetch Center
            center_response = requests.get(
                f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={dist_key}&date={new_date}",
                headers=header)
            centers_data = center_response.json()
            centers = pd.DataFrame(centers_data.get('centers'))

            if centers.empty:
                st.error('No Center found')
            else:
                session_ids = []
                for j, row in centers.iterrows():
                    session = pd.DataFrame(row['sessions'][0])
                    session['center_id'] = centers.loc[j, 'center_id']
                    session_ids.append(session)

                sessions = pd.concat(session_ids, ignore_index=True)
                av_centeres = centers.merge(sessions, on='center_id')

                ## Age filter
                if age == '18 & Above':
                    age_val = 18
                    av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                elif age == '18-45':
                    age_val = 45
                    av_centeres = av_centeres[av_centeres['max_age_limit'] == age_val]
                else:
                    age_val = 45
                    av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]

                av_centeres.drop(
                    columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to', 'state_name',
                                'district_name','max_age_limit', 'vaccine_fees'
                                , 'allow_all_age'], inplace=True, errors='ignore')

                ## Vaccine filter
                av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                ## Fees filter
                av_centeres = av_centeres[av_centeres['fee_type'] == fee]

                new_df = av_centeres.copy()
                new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode','Fee','Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Dose 1', 'Dose 2']
                new_df['Time'] = [i["time"] for i in new_df['Timing']]
                new_df.drop(columns = 'Timing', inplace = True)
                new_df = new_df[['Center_ID', 'Name', 'Fee','Pincode',
                                    'Availability', 'Minimum Age', 'Vaccine Type', 'Time', 'Address']]
                
            
                if new_df.empty:
                    st.error("No Center found.")
                else:
                    
                    st.dataframe(new_df) 
                    st.markdown(get_table_download_link(new_df,district_box.replace(' ','_')+'_'+new_date.replace('-','_')+'.csv','Download Report'), unsafe_allow_html=True)
                    href = f'<a href="https://selfregistration.cowin.gov.in/">Book Slot</a>'
                    st.markdown(href,unsafe_allow_html=True)
                     
    elif choice == 'Search by Pin':
        ## Area Pin
        area_pin = st.sidebar.text_input('Enter your Pin Code')
        col1, col2 = st.columns(2)
        with col1:
            ## Age
            age_display = ['18 & Above', '18-45', '45+']
            age = st.selectbox("Your Age", age_display)
            age_val = 0

            ## Select Date
            vac_date = st.date_input("Date")
            vac_date = str(vac_date).split('-')
            new_date = vac_date[2] + '-' + vac_date[1] + '-' + vac_date[0]

        with col2:
            ## Vaccine Type
            vacc_display = ['Covishield','Covaxin', 'Sputnik V']
            vaccine = st.selectbox("Vaccine Type", vacc_display)
            vaccine_type = ''
            if vaccine == 'Covishield':
                vaccine_type = 'COVISHIELD'
            elif vaccine == 'Covaxin':
                vaccine_type = 'COVAXIN'
            else:
                vaccine_type = 'SPUTNIK V'

            ## Fee Type
            fee_display = ['Free','Paid']
            fee = st.selectbox("Fee Type", fee_display)

        if st.button("Search"):
            center_response = requests.get(
                f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={area_pin}&date={new_date}",
                headers=header)
            centers_data = center_response.json()
            centers = pd.DataFrame(centers_data.get('centers'))
            if centers.empty:
                st.error('No Center found')
            else:
                session_ids = []
                for j, row in centers.iterrows():
                    session = pd.DataFrame(row['sessions'][0])
                    session['center_id'] = centers.loc[j, 'center_id']
                    session_ids.append(session)

                sessions = pd.concat(session_ids, ignore_index=True)
                av_centeres = centers.merge(sessions, on='center_id')
                print(av_centeres.columns)
                ## Age filter
                if age == '18 & Above':
                    age_val = 18
                    av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]
                elif age == '18-45':
                    age_val = 45
                    av_centeres = av_centeres[av_centeres['max_age_limit'] == age_val]
                else:
                    age_val = 45
                    av_centeres = av_centeres[av_centeres['min_age_limit'] == age_val]

                av_centeres.drop(
                    columns=['sessions', 'session_id', 'lat', 'block_name', 'long', 'date', 'from', 'to', 'state_name',
                             'district_name', 'max_age_limit', 'vaccine_fees'
                        , 'allow_all_age'], inplace=True, errors='ignore')

                ## Vaccine filter
                av_centeres = av_centeres[av_centeres['vaccine'] == vaccine_type]

                ## Fees filter
                av_centeres = av_centeres[av_centeres['fee_type'] == fee]

                new_df = av_centeres.copy()
                new_df.columns = ['Center_ID', 'Name', 'Address', 'Pincode','Fee','Availability', 'Minimum Age', 'Vaccine Type', 'Timing', 'Dose 1', 'Dose 2']
                new_df['Time'] = [i["time"] for i in new_df['Timing']]
                new_df.drop(columns = 'Timing', inplace = True)
                new_df = new_df[['Center_ID', 'Name', 'Fee','Pincode',
                                    'Availability', 'Minimum Age', 'Vaccine Type', 'Time', 'Address']]
                
                if new_df.empty:
                    st.error("No Center found.")
                else:
                    st.dataframe(new_df)
                    st.markdown(get_table_download_link(new_df,area_pin+ '_' + new_date.replace('-',
                                                                                                                '_') + '.csv',
                                                        'Download Report'), unsafe_allow_html=True)
                    href = f'<a href="https://selfregistration.cowin.gov.in/">Book Slot</a>'
                    st.markdown(href, unsafe_allow_html=True)

run()
