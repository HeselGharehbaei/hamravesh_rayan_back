from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
import re
from django.core.validators import validate_email
from django.utils.translation import gettext as _
from rest_framework import serializers
from datetime import datetime
from jdatetime import datetime as jalali_datetime
import smtplib
import dns.resolver


def validate_national_code(national_code):

    length_na_code = len(national_code)
    if length_na_code != 10:
        raise ValidationError('تعداد ارقام کد ملی مجاز نیست')
    sum_of_decimal = 0
    for i in range(length_na_code-1):
        sum_of_decimal += int(national_code[i]) *(length_na_code - i) 
    res = sum_of_decimal%11
    if res>=2:
        check_no = 11-res
    else:
        check_no = res
    if int(national_code[length_na_code-1]) != check_no:
        raise ValidationError('کد ملی صحیح نمی باشد')

    if national_code[:3] not in str(nathional_code_city):
        raise ValidationError('شناسه کد ملی وجود ندارد')
     

        
nathional_code_city = [
169,170,149,150,171,168,136,137,138,545,505,636,164,165,172,623,506,519,154,155,567,173,159,160,604,274,275,295,637,292,492,289,677,294,493,279,280,288,284,285,638,291,640,293,675,282,
283,286,287,296,297,290,400,401,404,405,397,398,399,647,502,584,402,403,392,393,395,396,386,387,503,444,551,447,561,445,718,'083',446,448,552,543,442,443,'051','052','053','058',
'055',617,'057',618, '059','060','061','062',544,'056',571,593,667,348,586,338,339,343,344,346,337,554,469,537,345,470,341,342,483,484,557,418,416,417,412,413,592,612,613,406,
407,421,598,419,385,420,528,213,214,205,206,498,568,711,217,218,221,582,483,625,576,578,227,208,209,225,577,712,215,216,626,627,579,713,499,222,219,220,500,501,623,497,223,689,
487,226, 224,486,211,212,628,202,203,531,488,261,273,630,264,518,631,258,259,570,265,268,269,653,517,569,267,262,263,593,266,693,271,272,694,270,516,333,334,691,323,322,595,
395,641,596,336, 335,496,337,324,325,394,330,332,331,687,422,423,599,600,688,424,425,426,550,697,384,377,378,558,385,646,375,376,372,373,379,380,383,674,381,382,676,722,542,
312,313,317,310,311,302,303,583,321,382,304,305,536,605,308,309,306,307,319,313,314,606,320,698,298,299,535,315,316,318,607,608,508,538,728,509,438,439,580,590,559,588,431,432,
'037','038',702,240,241,670,648,252,678,253,649,513,546,671,246,247,654,548,547,655,248,249,253,514,665,673,228,229,230,679,256,257,244,245,681,723,236,237,683,656,250,251,515,
242,243,238,239,657,255, 684,700,642,457,456,458,459,460,530,520,358,359,682,703,364,365,371,701,720,366,367,704,361,362,369,370,635,668, 533,705,699,669,725,597,611,525,181,
527,585,685,663,192-193,174,175,183,184,481,706,194,195,185,186,182	,199,200,198,662,190,191,692,189,707,526,187,188,729,730,196,197,661,680,643,562,572,'074',644,'072','073',
'069','070', 521,573,522,724,'076','077',650,574,'078','079','081','084',651,'086','087','089','090',553,'091','092','093','094','097', '098','096',105,106,'063','067','068',
'075',591,'082',635,524, 468,465,464,461,462,467,632,555,633,629,466,696,721,'064','065',523,652,719,716,'085','088',563,529,353,349,350,355,609,351,352,354,732,357,532,610,356,556,
658,'001','002','003','004','005','006','007','008','011','020','025','015','043',666,489,'044','045','048','049',490,491,695,659,'031','032',664,717,'041','042',471,472,454,581,
449,450,616,534,455,451,726,634,453,727,452,145,146,731,690,601,504,163,714,715,566,166,167,161,162,686,603,619,118,127,128,129,620,621,549,564,575,113,114,122,540,660,120,512,510,
511,119,115,112,110,111,125,126,565,121,116,117,541,622,124,108,109,123,428,427,507,158,615,152,153
]

phone_pattern_iran = r'^09\d{9}$'

def validate_phone_number(phone_number):
    if re.match(phone_pattern_iran, phone_number):
        return True
    return ValidationError('phone number is not valid')

def validate_email_is_exist_and_format(email):
    # Address used for SMTP MAIL FROM command.
    fromAddress = 'test@example.com'

    # Simple Regex for syntax checking.
    regex = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,})$'

    # Email address to verify.
    addressToVerify = str(email)

    # Syntax check.
    match = re.match(regex, addressToVerify)
    if match is None:
        raise ValidationError('Invalid syntax')
    # Get domain for DNS lookup.
    if '@gmail' in email:
        splitAddress = addressToVerify.split('@')
        domain = str(splitAddress[1])
        # MX record lookup.
        records = dns.resolver.resolve(domain, 'MX')
        mxRecords = [str(record.exchange) for record in records]
        # SMTP settings (disable debug output).
        server = smtplib.SMTP()
        # SMTP conversation.
        success = False
        for mxRecord in mxRecords:
            try:
                server.connect(mxRecord)
                server.helo(server.local_hostname)
                server.mail(fromAddress)
                code, message = server.rcpt(str(addressToVerify))
                if code == 250:
                    success = True
                    break
                server.quit()
            except Exception as e:
                raise ValueError(f"Unable to connect to {mxRecord}: {e}")

        if success:
            return True
        else:
            raise ValidationError('Email address is not valid')
    else:
        return True    


def username_validate_for_users(username):
    try:
        # Try to validate the value as an email
        validate_email_is_exist_and_format(username)
        return username
    except ValidationError:
        # If it's not a valid email, try to validate it as a phone number
        if not validate_phone_number(username):
            raise serializers.ValidationError(
                {'username': _('ایمیل یا شماره تلفن معتبر وارد کنید')},
                code='invalid'
                )
        return username
    
def dispatcher_username_validate_for_users(username):
    if not validate_phone_number(username):
        raise serializers.ValidationError(
            {'username': _('ایمیل یا شماره تلفن معتبر وارد کنید')},
            code='invalid'
            )
    return username
        
def validate_date_within_10_days_and_jalali_date_format(choises_date):

    choises_date = choises_date.replace("/", "-")
        # if not re.match(r'^\d{4}-\d{2}-\d{2}$', choises_date):
    try:
        # month = f"{int(month):02d}"
        # day = f"{int(day):02d}"
        # choises_date = f"{year}-{month}-{day}"  # بازسازی تاریخ
        jalali_date = jalali_datetime.strptime(choises_date, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(
            _('فرمت تاریخ اشتباه است YYYY/MM/DD.'),
            params={'value': choises_date},
                )
    parts = choises_date.split("-")
    year, month, day = parts
    if len(parts) != 3:
        raise ValidationError(
            _('فرمت تاریخ اشتباه است، روز، ماه یا سال وارد نشده است'),
            params={'value': choises_date},
        )
    # if not year.isdigit() or len(year) != 4:
    #     raise ValidationError(
    #         _('سال باید چهار رقمی باشد.'),
    #         params={'value': choises_date},
    #     )
    if not year.isdigit() or len(month) != 2:
        raise ValidationError(
            _('ماه باید دو رقمی باشد.'),
            params={'value': choises_date},
        )
    if not year.isdigit() or len(day) != 2:
        raise ValidationError(
            _('روز باید دو رقمی باشد.'),
            params={'value': choises_date},
        )

    gregorian_date= jalali_date.togregorian().date()
    today = datetime.today().date()
    days_diff = (gregorian_date - today).days  
    if days_diff > 10 or days_diff < 0:
        raise ValidationError(
            _('تاریخ جمع آوری باید تا ده روز آینده باشد.'),
            params={'value': choises_date},
        )
    return choises_date.replace("-", "/")

# def validate_jalali_date(value):
#     value = value.replace("/", "-")
#     try:
#         # Attempt to parse the value as a Jalali date
#         jalali_datetime.strptime(value, '%Y-%m-%d')
#         print(value)
#     except ValueError:
#         raise ValidationError(
#             _('Invalid Jalali date format. The date should be in the format YYYY-MM-DD.'),
#             params={'value': value},
#         )    