import smtplib

def authenticate_mail(user, password):
    smtpsrv = "smtp.office365.com"
    smtpserver = smtplib.SMTP(smtpsrv,587)    
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    try:
        smtpserver.login(user, password)
    except:
        return False
    return True







