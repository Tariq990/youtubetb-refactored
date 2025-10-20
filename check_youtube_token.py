"""
التحقق من صلاحية توكن YouTube وتجديده إذا لزم الأمر
"""
import json
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def check_youtube_token():
    """التحقق من صلاحية توكن YouTube"""
    
    token_path = Path("secrets/token.json")
    
    if not token_path.exists():
        print("❌ ملف token.json غير موجود!")
        print("   يجب تشغيل YouTube upload مرة واحدة للحصول على التوكن")
        return False
    
    try:
        # قراءة التوكن
        with open(token_path, 'r') as f:
            token_data = json.load(f)
        
        # عرض معلومات التوكن
        print("\n" + "="*60)
        print("📊 معلومات توكن YouTube")
        print("="*60)
        
        expiry_str = token_data.get('expiry')
        if expiry_str:
            # Parse expiry time with timezone awareness
            expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            # Make 'now' timezone-aware to match expiry
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            print(f"⏰ تاريخ الانتهاء: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if expiry > now:
                remaining = expiry - now
                hours = remaining.total_seconds() / 3600
                print(f"✅ التوكن صالح - متبقي: {hours:.1f} ساعة")
                return True
            else:
                print("⚠️  التوكن منتهي الصلاحية!")
                
                # محاولة التجديد
                print("\n🔄 محاولة تجديد التوكن...")
                
                creds = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes')
                )
                
                if creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        
                        # حفظ التوكن الجديد
                        new_token_data = {
                            'token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'token_uri': creds.token_uri,
                            'client_id': creds.client_id,
                            'client_secret': creds.client_secret,
                            'scopes': creds.scopes,
                            'universe_domain': token_data.get('universe_domain', 'googleapis.com'),
                            'account': token_data.get('account', ''),
                            'expiry': creds.expiry.isoformat()
                        }
                        
                        with open(token_path, 'w') as f:
                            json.dump(new_token_data, f)
                        
                        new_expiry = creds.expiry
                        new_remaining = new_expiry - now
                        new_hours = new_remaining.total_seconds() / 3600
                        
                        print(f"✅ تم تجديد التوكن بنجاح!")
                        print(f"⏰ صالح حتى: {new_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"⏳ متبقي: {new_hours:.1f} ساعة")
                        return True
                        
                    except Exception as e:
                        print(f"❌ فشل تجديد التوكن: {e}")
                        print("\n💡 الحل:")
                        print("   1. احذف ملف secrets/token.json")
                        print("   2. شغل البايب لاين مرة واحدة")
                        print("   3. سيطلب منك تسجيل الدخول إلى YouTube")
                        return False
                else:
                    print("❌ لا يوجد refresh_token - يجب إعادة المصادقة")
                    print("\n💡 الحل:")
                    print("   1. احذف ملف secrets/token.json")
                    print("   2. شغل البايب لاين مرة واحدة")
                    print("   3. سيطلب منك تسجيل الدخول إلى YouTube")
                    return False
        else:
            print("⚠️  لا يوجد تاريخ انتهاء في التوكن")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في قراءة التوكن: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    print("\n🔍 فحص صلاحية توكن YouTube...\n")
    
    is_valid = check_youtube_token()
    
    print("\n" + "="*60)
    if is_valid:
        print("✅ النتيجة: التوكن صالح وجاهز للاستخدام")
    else:
        print("❌ النتيجة: التوكن غير صالح - يحتاج إعادة مصادقة")
    print("="*60 + "\n")
    
    sys.exit(0 if is_valid else 1)
