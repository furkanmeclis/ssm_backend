from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.exceptions import ParseError

from utils.api_responses import ApiResponse
from utils.ai_utils import extract_text_from_image, call_openai_chat, is_valid_message
# from rest_framework.throttling import UserRateThrottle

class SimpleChatView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]
    # throttle_classes = [UserRateThrottle]
    # throttle_scope = 'ai_chat'

    def post(self, request, *args, **kwargs):
        user_message = request.data.get('message')

        if not user_message:
            return ApiResponse.BadRequest(message="Lütfen bir mesaj girin ('message' alanı eksik).")

        if not is_valid_message(user_message):
             return ApiResponse.BadRequest(message="Mesajınız uygunsuz içerik barındırıyor.")

        system_prompt = """
          Sen 'Sınav Soruları' adlı uygulamada deneyimli ve bilgili bir öğretmensin.
          Kullanıcıların sorularına kibar, samimi, kısa ve öz şekilde yanıtlar ver. Amacın, öğrencilere yol göstermek, bilgi vermek ve motive etmektir.
          Karmaşık konuları bile sade bir dille açıklayarak destek ol. Gereksiz detaylardan kaçın, net ve anlaşılır cevaplar ver.
          Ancak, uygunsuz, saldırgan veya etik dışı soruları yanıtlamamalısın. Eğer kullanıcı sistemi kötüye kullanmaya çalışırsa veya aldatıcı sorular sorarsa, kibarca uyar ve konuyu değiştirmeye yönlendir.
          Yanıt verirken, her zaman platformun amacına uygun, saygılı ve eğitici bir üslup kullan.
        """

        try:
            ai_response = call_openai_chat(system_prompt, user_message)
            return ApiResponse.Success(data={"response": ai_response})
        except RuntimeError as e:
            # Catch errors raised from utils (OCR, API call issues)
            return ApiResponse.BadRequest(message=str(e))
        except Exception as e:
            print(f"Unexpected error in SimpleChatView: {e}")
            return ApiResponse.BadRequest(message="Sohbet yanıtı alınırken beklenmedik bir hata oluştu.")

class SummarizeImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    # throttle_classes = [UserRateThrottle]
    # throttle_scope = 'ai_image'

    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return ApiResponse.BadRequest(message="Lütfen bir görüntü dosyası yükleyin ('image' alanı eksik).")

        image_file = request.FILES['image']

        try:
            # 1. Extract Text via OCR
            extracted_text = extract_text_from_image(image_file)
            if not extracted_text or extracted_text.strip() == "":
                 return ApiResponse.BadRequest(message="Görüntüden metin çıkarılamadı veya metin boş.")

            if not is_valid_message(extracted_text):
                 return ApiResponse.BadRequest(message="Görüntüdeki metin uygunsuz içerik barındırıyor.")

            # 2. Summarize with OpenAI
            system_prompt = """
              Sen 'Sınav Soruları' adlı uygulamada bir deneyimli bir öğretmensin.
              Verilen metni sadece özetle. Metnin genel içeriğini ve ana fikrini kısaca belirt.
              Kesinlikle çoktan seçmeli sorulara cevap verme, seçeneklerden birini seçme, veya doğru cevabı tahmin etme.
              Kullanıcıya doğru yanıt sunma, sadece metnin genel içeriğini özetle. Özetin kısa ve anlaşılır olsun.
            """
            summary = call_openai_chat(system_prompt, extracted_text)
            return ApiResponse.Success(data={"summary": summary, "extracted_text": extracted_text})

        except RuntimeError as e:
            return ApiResponse.BadRequest(message=str(e)) # OCR or API call errors
        except Exception as e:
            print(f"Unexpected error in SummarizeImageView: {e}")
            return ApiResponse.BadRequest(message="Görüntü özeti oluşturulurken beklenmedik bir hata oluştu.")

class SolveImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    # throttle_classes = [UserRateThrottle]
    # throttle_scope = 'ai_image'

    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return ApiResponse.BadRequest(message="Lütfen bir görüntü dosyası yükleyin ('image' alanı eksik).")

        image_file = request.FILES['image']

        try:
            # 1. Extract Text via OCR
            extracted_text = extract_text_from_image(image_file)
            if not extracted_text or extracted_text.strip() == "":
                 return ApiResponse.BadRequest(message="Görüntüden metin çıkarılamadı veya metin boş.")

            if not is_valid_message(extracted_text):
                 return ApiResponse.BadRequest(message="Görüntüdeki metin uygunsuz içerik barındırıyor.")

            # 2. Solve with OpenAI
            system_prompt = f"""
              Sen 'Sınav Soruları' adlı uygulamada deneyimli bir öğretmensin. Kullanıcıların sorularına kibar, kısa ve öz şekilde yanıt ver.
              Ancak, etik dışı veya uygunsuz içerikleri yanıtlamamalısın.
              Aşağıdaki metinde yer alan soruyu dikkatlice oku ve çöz. Çözümü adım adım ve anlaşılır bir şekilde açıkla. Eğer bir çoktan seçmeli soru ise, doğru seçeneği belirt ve neden doğru olduğunu açıkla. Diğer seçeneklerin neden yanlış olduğunu da kısaca belirtebilirsin.

              Metin/Soru:
              ---
              {extracted_text}
              ---

              Lütfen yukarıdaki soruya odaklanarak çözümünü sun.
            """
            # Use the extracted text itself as the user message here
            solution = call_openai_chat(system_prompt, "Yukarıdaki soruyu çözebilir misin?") # Simple trigger phrase
            return ApiResponse.Success(data={"solution": solution, "extracted_text": extracted_text})

        except RuntimeError as e:
            return ApiResponse.BadRequest(message=str(e)) # OCR or API call errors
        except Exception as e:
            print(f"Unexpected error in SolveImageView: {e}")
            return ApiResponse.BadRequest(message="Görüntüdeki soru çözülürken beklenmedik bir hata oluştu.")
