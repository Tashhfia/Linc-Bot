# This files contains the custom actions which can be used to run a custom Python code.


from typing import Any, Text, Dict, List, Optional

import mysql.connector
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.events import (SlotSet, AllSlotsReset, ConversationPaused, ConversationResumed)
from rasa_sdk.types import DomainDict
from actions.my_database import addToMailingList, checkMailingList, addToHandoffReq, addToBookingList, \
    checkBookingList, deleteFromBookingList, deleteFromMalingList, menuQuery
from datetime import datetime as dt
from datetime import time


# email subscription form validation
class ValidateEmailSubscriptionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_email_subscription_form"

    def validate_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """ validate user's email address and check if its already on the mailing list"""
        try:
            email = tracker.get_slot("email")

            if email is not None:
                try:
                    alreadyExists = checkMailingList(email)
                    if alreadyExists:
                        dispatcher.utter_message(response="utter_already_signedup")
                    else:
                        dispatcher.utter_message(response="utter_thank_email")
                        addToMailingList(tracker.get_slot("email"))
                except (mysql.connector.ProgrammingError, mysql.connector.Error, mysql.connector.DataError,
                        mysql.connector.PoolError):
                    dispatcher.utter_message(
                        text="Ooops! I'm encountering some connection error with our mailing database."
                             " Please try again later...")
                return {}

            else:
                dispatcher.utter_message(text="I'm sorry, I couldn't recognize your email. "
                                              "Can you type it in again?")
                return {"email": None}

        except:
            dispatcher.utter_message(text="I'm sorry, I couldn't recognize your email. "
                                          "Can you type it in again?")
            return {"email": None}



class SubmitEmailSubscriptionForm(Action):
    """Submits the user's details into the database"""

    def name(self) -> Text:
        return "action_submit_email_subscription_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        print('submitted mail')
        dispatcher.utter_message(response="utter_mailing_slots")

        return [AllSlotsReset()]


class ValidateCancelMailingSubscriptionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cancel_mailing_subscription_form"

    def validate_mailing_email(
                self,
                slot_value: Any,
                dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: DomainDict,
        ) -> Dict[Text, Any]:
        """Here we get the email entity and set slot"""
        k = 'email'
        try:
            if k == tracker.latest_message['entities'][0]['entity']:
                dispatcher.utter_message(text="Got your email address {0}".format
                (tracker.latest_message['entities'][0]['value']))
                return {"mailing_email": tracker.latest_message['entities'][0]['value']}

            else:
                print("entity not found,")
                dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                    tracker.latest_message['text']))
                return {"mailing_email": None}
        except:
            dispatcher.utter_message(text="I'm not sure what you're trying to say... Please rephrase.")
            return {"mailing_email": None}


class SubmitCancelMailingSubscriptionForm(Action):
    """Deletes record  if email exists in the database"""

    def name(self) -> Text:
        return "action_submit_cancel_mailing_subscription_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        try:
            email = tracker.get_slot('mailing_email')
            is_sure = tracker.get_slot('reconfirm_cancel')

            if is_sure:

                try:
                    emailExists = checkMailingList(email)

                    if emailExists[0]:
                        deleteFromMalingList(email)
                        dispatcher.utter_message(
                            text="I have successfully removed your email address {0} from our mailing list.".format(email))
                    else:
                        dispatcher.utter_message(text="I couldn't find your email address {0} in our mailing list ".format(email))
                except (mysql.connector.ProgrammingError, mysql.connector.Error, mysql.connector.DataError,
                        mysql.connector.PoolError):
                    dispatcher.utter_message(text='Whoops! I encountered some connectivity issues while trying to access '
                                                  'our database. Please try again later....')
            else:
                dispatcher.utter_message(text='Glad you changed your mind...!')

        except:
            dispatcher.utter_message(text='Whoopsie! I encountered some issue while submitting your request.'
                                          ' Please try again later....')
            dispatcher.utter_message(text='For urgent issues please email us at linc@help.com. Sorry for the '
                                          'inconvenience caused....')

        return [AllSlotsReset()]


# human hand off form details validation
class ValidateHumanHandoffForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_human_handoff_form"

    def validate_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """ validate user's email address """
        try:
            email = tracker.get_slot("email")
            print('--------------------------')
            print(email)

            if email is not None:
                dispatcher.utter_message(text="Got your email address {0}!".format(email))
                return {}

            else:
                dispatcher.utter_message(text="I'm sorry, I couldn't recognize your email. "
                                              "Can you type it in again?")
                return {"email": None}
        except:
            dispatcher.utter_message(text="I'm sorry, I couldn't recognize your email. "
                                          "Can you type it in again?")
            return {"email": None}


    def validate_issue(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        issue = slot_value
        if len(issue) < 10:
            dispatcher.utter_message(text="Please elaborate a bit more..")
            return {"issue": None}
        elif len(issue) > 250:
            dispatcher.utter_message(text="Please limit your message between 1 to 5 sentences...")
            return {"issue": None}
        else:
            dispatcher.utter_message(text="Noted with thanks")
            return{"issue": issue}

    def validate_issue_urgency(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        urgency = slot_value
        print(urgency)
        urgencyVals = ["High", "Moderate", "Low"]
        if urgency is None or urgency not in urgencyVals:
            dispatcher.utter_message(text="That is not a valid urgency level."
                                          "Please enter a valid urgency level for your issue.")
            return {"issue_urgency": None}
        else:
            dispatcher.utter_message(text="Thank you for the information.")
            return {}


class SubmitHumanHandoffReq(Action):
    """Submits the user's details into the database"""

    def name(self) -> Text:
        return "action_submit_human_handoff_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        try:
            print('submitted handoff')
            addToHandoffReq(tracker.get_slot("email"), tracker.get_slot("issue"), tracker.get_slot("issue_urgency"))
            dispatcher.utter_message(response="utter_human_handoff_form_submitted")
        except:
            dispatcher.utter_message(text='Whoopsie! I encountered some issue while submitting your request.'
                                          ' Please try again later....')
            dispatcher.utter_message(text='For urgent issues please email us at linc@help.com. Sorry for the '
                                          'inconvenience caused....')
        return [AllSlotsReset()]


class ValidateBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_booking_form"

    def validate_book_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        """Validates if user's requested time is valid or not."""

        openingTime = time(9, 0)
        closingTime = time(21, 30)

        try:
            entity_time = slot_value  # getting entity from last user message
            timeFormat = "%H:%M"
            time_obj = dt.fromisoformat(entity_time)
            time_string = time_obj.strftime(
                "%H:%M")  # Hour (24-hour clock) as a zero-padded decimal number.	00, 01, ..., 23
            # Minute as a zero-padded decimal number.	00, 01, ..., 59
            print(time_obj)
            print(time_string)
            print('*************************')

            dt.strptime(time_string, timeFormat)

            print('correct!')

            if openingTime < dt.strptime(time_string, timeFormat).time() < closingTime:
                print(dt.strptime(time_string, timeFormat).time())
                dispatcher.utter_message(text="Got your booking time: {0}".format(time_string))
                return{'book_time': time_string}
            else:
                dispatcher.utter_message(text="We aren't open at {0}, please try again...".format(time_string))
                print('wrong')
                return {'book_time': None}

        except:
            print("This is the incorrect date string format.")
            dispatcher.utter_message(text="Looks like your time format is incorrect, it should be hh:mm")
            return {'book_time': None}

    def validate_book_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        """Validates if user's requested date format is valid
        or not. Also checks database for availability"""

        future = dt.strptime('01-02-2023', '%d-%m-%Y')      # Date for which we don't have info about yet
        present = dt.now().date()                           # current date
        print(present)
        print('*****************************************************')

        try:
            entity_val = tracker.latest_message['entities'][0]['value']  # getting entity from last user message
            print(tracker.latest_message['entities'])
            print(tracker.latest_message['entities'][0])
            print(entity_val)
            print(type(entity_val))
            print('****************************************************')

            req_date = dt.fromisoformat(entity_val)  # extract just date potion and convert to date time object
            req_date_str = req_date.strftime('%d-%m-%Y')  # returns requested date in string format
            print(req_date.strftime('%d-%m-%Y'))
            print('****************************************************')

            dt.strptime(req_date_str, "%d-%m-%Y")           # checks if format is correct

            print("This is the correct date string format.")
            # if pr < dt.strptime(date, "%d-%m-%Y").date():
            if present < req_date.date() < future.date():
                print('yay')
            # check database here .....................................
                dispatcher.utter_message(text="Got your booking date: {0}".format(req_date_str))
                return {"book_date": req_date_str}

            elif present == req_date.date():                # can't accept last minute reservation
                print('cant take last minute')
                dispatcher.utter_message(text="I'm sorry, I can't take last minute reservations."
                                                  "Please contact our customer service team for last minute booking at"
                                                  "+60123456789")
                return {"book_date": None}
            elif req_date.date() > future.date():           # date too far in the future
                print("too far in the future")
                dispatcher.utter_message(text="I'm sorry, I don't have the availability details about your"
                                                  " requested date {0} yet.....".format(req_date_str))
                return {"book_date": None}

            else:
                print('sad')
                dispatcher.utter_message(
                text="Are you sure your date: {0} is correct? Please try again with the correct format dd-mm-yyyy".
                    format(req_date_str))
                return {"book_date": None}

        except ValueError:
            print("This is the incorrect date string format. It should be DD-MM-YYYY")
            dispatcher.utter_message(text="Looks like your date format is incorrect, it should be dd-mm-yyyy")
            return{"book_date": None}
        except:
            print("This is the incorrect date string format. It should be DD-MM-YYYY")
            dispatcher.utter_message(text="Are you sure your booking date is in the right format? "
                                          "Please use this DD-MM-YYYY format...")
            return{"book_date": None}

    def validate_booking_email(
                self,
                slot_value: Any,
                dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: DomainDict,
        ) -> Dict[Text, Any]:
        """Here we set the email address for the user's reservation"""
        k = 'email'
        try:
            if k == tracker.latest_message['entities'][0]['entity']:
                dispatcher.utter_message(text="Your details will be sent to you "
                                               "at {0}".format(tracker.latest_message['entities'][0]['value']))
                return {"booking_email": tracker.latest_message['entities'][0]['value']}

            else:
                print("entity not found,")
                dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                    tracker.latest_message['text']))
                return {"booking_email": None}
        except:
            if k == tracker.latest_message['entities'][0]['entity']:
                dispatcher.utter_message(text="Your details will be sent to you "
                                              "at {0}".format(tracker.latest_message['entities'][0]['value']))
                return {"booking_email": tracker.latest_message['entities'][0]['value']}

            else:
                print("entity not found,")
                dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                    tracker.latest_message['text']))
                return {"booking_email": None}


class SubmitBookingForm(Action):
    """Submits the user's details into the database"""

    def name(self) -> Text:
        return "action_submit_booking_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        try:
            addToBookingList(tracker.get_slot("book_date"), tracker.get_slot("book_time"),
                             tracker.get_slot("booking_email"))
            dispatcher.utter_message(text=
                                     "Successfully created a booking for you on {0} at {1}. Check your email {2} for details".
                                     format(tracker.get_slot("book_date"), tracker.get_slot("book_time"),
                                            tracker.get_slot("booking_email")))
            dispatcher.utter_message(response="utter_booking_form_submitted")
        except:
            dispatcher.utter_message(text="Whoops ran into an error while handling your request. "
                                          "Please email us at linc@help.com. Sorry for the inconvenience caused....")
        return [AllSlotsReset()]


# validate info for checking booking status
class ValidateCheckReservationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_check_reservation_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        additional_slots = []
        if tracker.slots.get("remember_bookdate") is True:
            # If user remembers ask booking date else we will find using
            # booking email only
            print('TRUEEEEEE')
            additional_slots.append("check_booking_date")

        return slots_mapped_in_domain + additional_slots

    async def extract_check_booking_date(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        try:
            entity_val = tracker.latest_message['entities'][0]['value']  # getting entity from last user message
            print(tracker.latest_message['entities'])
            print(tracker.latest_message['entities'][0])
            print(entity_val)
            print(type(entity_val))
            print('****************************************************')

            req_date = dt.fromisoformat(entity_val)  # extract just date potion and convert to date time object
            req_date_str = req_date.strftime('%d-%m-%Y')  # returns requested date in string format
            print(req_date.strftime('%d-%m-%Y'))
            print('****************************************************')

            dt.strptime(req_date_str, "%d-%m-%Y")  # checks if format is correct

            print("This is the correct date string format.")
            dispatcher.utter_message(text="Thank you for entering your booking date {0} in the correct format".
                                     format(req_date_str))
            print('slot set!')
            return {"check_booking_date": req_date_str}

        except:
            print("This is the incorrect date string format. It should be DD-MM-YYYY")
            dispatcher.utter_message(text="Looks like your date format is incorrect, it should be dd-mm-yyyy")
            return {"check_booking_date": None}

    def validate_booking_email(
                self,
                slot_value: Any,
                dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: DomainDict,
        ) -> Dict[Text, Any]:
        """Here we get the email address to check user's reservation"""
        k = 'email'
        try:
            if k == tracker.latest_message['entities'][0]['entity']:
                dispatcher.utter_message(text="Got your email address {0}".format(tracker.latest_message['entities'][0]['value']))
                return {"booking_email": tracker.latest_message['entities'][0]['value']}

            else:
                print("entity not found,")
                dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                    tracker.latest_message['text']))
                return {"booking_email": None}

        except:
            print("entity not found,")
            dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                tracker.latest_message['text']))
            return {"booking_email": None}


# check booking status
class SubmitCheckReservationForm(Action):
    """Submits the user's details into the database"""

    def name(self) -> Text:
        return "action_submit_check_reservation_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        try:
            email = tracker.get_slot("booking_email")
            slots = tracker.slots
            remembers = tracker.get_slot('remember_bookdate')
            print(remembers)

            if remembers:
                entity_val = tracker.latest_message['entities'][0]['value']  # getting entity from last user message
                print(tracker.latest_message['entities'][0])
                print('****************************************************')

                req_date = dt.fromisoformat(entity_val)  # extract just date potion and convert to date time object
                date = tracker.get_slot('check_booking_date')

                print(date)
                exists = checkBookingList(email, date)
                print('============')
                print(exists[0])

                if exists[0]:
                    dispatcher.utter_message(text="You have a booking on {0} at {1}.".format(date, exists[1]))
                else:
                    dispatcher.utter_message(text="I don't see any booking on {0} for the email address {1}".format
                    (date, email))

            else:
                exists = checkBookingList(email)

                if exists[0]:
                    if len(exists[1]) == 1:
                        dispatcher.utter_message(text="Found one booking for {0}".format(email))
                        dispatcher.utter_message(text="I found a booking on {0} at {1}".format(
                            exists[1][0][0], exists[1][0][1]))
                    else:
                        dispatcher.utter_message(text="Found {0} bookings for {1}".format(len(exists[1]), email))
                        for booking in range(len(exists[1])):
                            dispatcher.utter_message(text="Booking on {0} at {1}".format
                            (exists[1][booking][0], exists[1][booking][1]))

                else:
                    dispatcher.utter_message(text="I don't see any booking listed for the email address {0}".format
                    (email))
        except:

            dispatcher.utter_message(text="Whoops ran into an error while handling your request. "
                                          "Please email us at linc@help.com. Sorry for the inconvenience caused....")

        return [AllSlotsReset()]


# cancel booking
class ValidateCancelReservationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cancel_reservation_form"

    def validate_booking_email(
                self,
                slot_value: Any,
                dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: DomainDict,
        ) -> Dict[Text, Any]:
        """Here we get the email address to check user's reservation"""
        k = 'email'
        try:
            if k == tracker.latest_message['entities'][0]['entity']:
                dispatcher.utter_message(text="Got your email address {0}".format
                (tracker.latest_message['entities'][0]['value']))
                return {"booking_email": tracker.latest_message['entities'][0]['value']}

            else:
                print("entity not found,")
                dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                    tracker.latest_message['text']))
                return {"booking_email": None}
        except:
            print("entity not found,")
            dispatcher.utter_message(text="I'm not sure what {0} means. Please try again...".format(
                tracker.latest_message['text']))
            return {"booking_email": None}

    def validate_booking_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        """Validates if user's requested date format is valid
        or not. Also checks database for availability"""

        future = dt.strptime('01-02-2023', '%d-%m-%Y')      # Date for which we don't have info about yet
        present = dt.now().date()                           # current date
        print(present)
        print('*****************************************************')

        try:
            entity_val = tracker.latest_message['entities'][0]['value']  # getting entity from last user message
            print(tracker.latest_message['entities'])
            print(tracker.latest_message['entities'][0])
            print(entity_val)
            print(type(entity_val))
            print('****************************************************')

            req_date = dt.fromisoformat(entity_val)  # extract just date potion and convert to date time object
            req_date_str = req_date.strftime('%d-%m-%Y')  # returns requested date in string format
            print(req_date.strftime('%d-%m-%Y'))
            print('****************************************************')

            dt.strptime(req_date_str, "%d-%m-%Y")           # checks if format is correct

            print("This is the correct date string format.")
            # if pr < dt.strptime(date, "%d-%m-%Y").date():
            if present < req_date.date() < future.date():
                print('yay')
            # check database here .....................................
                return {"booking_date": req_date_str}

            elif present == req_date.date():                # can't accept last minute reservation
                print('cant take last minute')
                dispatcher.utter_message(text="I'm sorry, I can't help you with last minute cancellations."
                                            "Please contact our customer service team for last minute cancellations "
                                              "at +60123456789")
                return {"booking_date": None}
            elif req_date.date() > future.date():           # date too far in the future
                print("too far in the future")
                dispatcher.utter_message(text="Are you sure you remember your booking date correctly? Because I don't"
                                              " have booking information for this date yet....")
                return {"booking_date": None}

            else:
                print('sad')
                dispatcher.utter_message(
                text="Are you sure your date: {0} is correct? Please try again with the correct format dd-mm-yyyy".format
                (req_date_str))
                return {"booking_date": None}

        except:
            print("This is the incorrect date string format. It should be DD-MM-YYYY")
            dispatcher.utter_message(text="Looks like your date format is incorrect, it should be dd-mm-yyyy")
            return{"booking_date": None}


class SubmitCancelReservationForm(Action):
    """Submits the user's details into the database"""

    def name(self) -> Text:
        return "action_submit_cancel_reservation_form"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        try:
            email = tracker.get_slot('booking_email')
            booking_date = tracker.get_slot("booking_date")
            is_sure = tracker.get_slot('reconfirm_cancel')

            if is_sure:
                bookingExists = checkBookingList(email, booking_date)

                if bookingExists[0]:
                    deleteFromBookingList(email, booking_date)
                    dispatcher.utter_message(text="I have successfully cancelled your booking on {0}.".format(booking_date))
                else:
                    dispatcher.utter_message(text="I couldn't find any booking on {0} under this email {1} ".format(
                        booking_date, email))
            else:
                dispatcher.utter_message(text="Glad you changed your mind. Looking forward to see you at our restaurant!")
        except:
            dispatcher.utter_message(text="Whoops ran into an error while handling your request. "
                                          "Please email us at linc@help.com. Sorry for the inconvenience caused....")

        return [AllSlotsReset()]


class ExplainSlot(Action):
    """Provides explanation based on current slot in forms"""

    def name(self) -> Text:
        return "action_explain_slot"

    def run(
            self,
            dispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        try:
            slot = tracker.get_slot('requested_slot')
            print(slot)
            if slot == 'email':
                print('success')
                dispatcher.utter_message(response='utter_explain_email')
            elif slot == 'remember_bookdate':
                dispatcher.utter_message(response='utter_explain_remember_bookdate')
            elif slot == 'issue_urgency':
                dispatcher.utter_message(response='utter_explain_issue_urgency')
            elif slot == 'issue':
                dispatcher.utter_message(response='utter_explain_issue')
            elif slot == 'email':
                dispatcher.utter_message(response='utter_explain_email')
            elif slot == 'booking_email':
                dispatcher.utter_message(response='utter_explain_booking_email')
            elif slot == 'book_time':
                dispatcher.utter_message(response='utter_explain_book_time')
            elif slot == 'remember_bookdate':
                dispatcher.utter_message(text="It'll help me to find your reservation details faster")
            elif slot == 'book_date':
                dispatcher.utter_message(response='utter_explain_book_date')
            elif slot == 'check_booking_date':
                dispatcher.utter_message(response='utter_explain_check_booking_date')
            elif slot == 'booking_date':
                dispatcher.utter_message(response='utter_explain_booking_date')
            elif slot == 'mailing_email':
                dispatcher.utter_message(response='utter_explain_mailing_email')
            elif slot == 'reconfirm_cancel':
                dispatcher.utter_message(response='utter_explain_reconfirm_cancel')
            else:
                dispatcher.utter_message(text="Can you rephrase please?")
            return []
        except:
            dispatcher.utter_message(text="Can you rephrase your question please?")
            return []


class SlotReset(Action):

    def name(self) -> Text:
        return "action_slot_reset"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
        ) -> List[Dict[Text, Any]]:

        return [AllSlotsReset()]


class ShowMenu(Action):

    def name(self) -> Text:
        return "action_show_menu"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
        ) -> List[Dict[Text, Any]]:
        menu = ['salad', 'soup', 'burger', 'pasta', 'pizza', 'dessert', 'beverages']
        try:
            preference = tracker.latest_message['entities'][0]['value']
            print(preference)

            if preference is not None:
                if preference not in menu:
                    dispatcher.utter_message(response='utter_menu_pref_not_identified')
                elif preference == 'soup':
                    dispatcher.utter_message(response='utter_soup')
                elif preference == 'salad':
                    dispatcher.utter_message(response='utter_salad')
                elif preference == 'burger':
                    dispatcher.utter_message(response='utter_burgers')
                elif preference == 'pasta' or preference == 'pizza':
                    dispatcher.utter_message(response='utter_pizza_pasta')
                elif preference == 'dessert' or preference == 'beverages':
                    dispatcher.utter_message(response='utter_bev')
            else:
                dispatcher.utter_message(response='utter_menu_pref_not_identified')
        except:
            dispatcher.utter_message(response='utter_show_menu')
        return [SlotSet('menu_pref', None)]


class GeneralQuery(Action):

    def name(self) -> Text:
        return "action_general_query"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
        ) -> List[Dict[Text, Any]]:
        available_info = ['healthy', 'allergen', 'vegan', 'popular']

        try:
            query = tracker.get_slot('food_info')
            print(tracker.latest_message['entities'])
            dispatcher.utter_message(text="Wait a second, I am fetching information about our {0} items".format(
                query.lower()))
            print(000000000000000000000000000)
            print(tracker.get_slot('food_info'))

            if query.lower() not in available_info:
                dispatcher.utter_message(text="Whoopsie!! I don't think I have the information to answer that question....")
                dispatcher.utter_message(response="utter_menu_query_general")
            elif query == available_info[0]:
                healthy_items = menuQuery(query)
                dispatcher.utter_message(text="These are our low calorie items:")
                dispatcher.utter_message(text="{0}:{1} calories per serving \n{2}:{3} calories per serving \n{4}:{5} calories per serving \n".format(
                    healthy_items[0][0], healthy_items[0][1], healthy_items[1][0], healthy_items[1][1], healthy_items[2][0], healthy_items[2][1]))

            elif query == available_info[1]:
                dispatcher.utter_message(text="Some items of our may contain peanuts, shellfish, dairy and gluten. For"
                                              " more details please ask me this question again, but mention the name of"
                                              " the item you're interested about this time.... ")
            elif query == available_info[2]:
                vegan_items = menuQuery(query)
                print(0000000000000000000000000)
                print("1. {0} \n 2. {1}".format(vegan_items[0][0], vegan_items[1][0]))
                dispatcher.utter_message(text="These are our vegan items:\n 1. {0}\n 2. {1}\n 3. {2}\n".format(
                    vegan_items[0][0], vegan_items[1][0], vegan_items[2][0]))

            elif query == available_info[3]:
                popular_items = menuQuery(query)
                dispatcher.utter_message(text="These are our bestsellers:")
                dispatcher.utter_message(text="1. {0}\n2. {1}\n3. {2}\n4. {3}\n5. {4}".format(
                    popular_items[0][2][0], popular_items[1][0][0], popular_items[1][1][0],
                    popular_items[1][2][0], popular_items[1][3][0]))

        except:
            dispatcher.utter_message(text="Whoopsie!! I don't think I have the information to answer that question....")
            dispatcher.utter_message(response="utter_menu_query_general")

        return [SlotSet('food_info', None)]


class SpecificQuery(Action):

    def name(self) -> Text:
        return "action_specific_query"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
        ) -> List[Dict[Text, Any]]:
        available_info = ['healthy', 'allergen', 'vegan']
        try:
            query = tracker.get_slot('food_info')
            print(query)
            queryItem = tracker.get_slot('menuItems')
            dispatcher.utter_message(text="Wait a second, I am fetching information for your request".format(
                query.lower()))
            print(000000000000000000000000000)
            print(tracker.get_slot('food_info'), queryItem)

            if query.lower() not in available_info:
                dispatcher.utter_message(text="Whoopsie!! I don't think I have the information to answer that question."
                                              " I can provide you an allergen list, tell you about the amount of "
                                              "calories per serving and tell you whether the dish is vegan friendly or"
                                              " not....")
            elif query.lower() == available_info[0]:
                healthy_items = menuQuery(query, queryItem)
                print(healthy_items[0])
                dispatcher.utter_message(text="Our {0} contains {1} calories per serving".format(queryItem,
                                                                                                 healthy_items[0]))

            elif query.lower() == available_info[1]:
                allergens = menuQuery(query, queryItem)

                if len(allergens) == 0:
                    dispatcher.utter_message(text="Some items of our may contain peanuts, shellfish, dairy and gluten. For"
                                                  " more details please ask me this question again, but mention the name of"
                                                  " the item you're interested in this time.... ")
                else:
                    print(allergens[0])
                    dispatcher.utter_message(text="Our {0} contains these allergens {1}".format(queryItem,
                                                                                                allergens[0]))
            elif query.lower() == available_info[2]:
                vegan_items = menuQuery(query, queryItem)
                if vegan_items:
                    dispatcher.utter_message(text="Our {0} is 100% vegan...".format(queryItem))
                else:
                    dispatcher.utter_message(text="Unfortunately, our {0} is not vegan friendly...".format(queryItem))

        except:
            dispatcher.utter_message(text='Whoops, ran into some error while handling your request. '
                                          'Please check if you entered the name of the food item correctly....')

        return [SlotSet('food_info', None), SlotSet('menuItems', None)]


class FormJob(Action):

    def name(self) -> Text:
        return "action_form_job"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: DomainDict,
        ) -> List[Dict[Text, Any]]:
        try:
            slot = tracker.get_slot("requested_slot")
            print(slot)
            if slot is not None:
                dispatcher.utter_message(response="utter_tell_job_form")
            else:
                dispatcher.utter_message(response="utter_tell_job")
        except:
            dispatcher.utter_message(response="utter_tell_job")
