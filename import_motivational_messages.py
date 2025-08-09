import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osym_backend.settings')
django.setup()

from quizzes.models import MotivationalMessage
from questions.models import Subject

range_mapping = {
    '0-20': 1,
    '20-40': 2,
    '40-60': 3, 
    '60-80': 4,
    '80-100': 5
}

# Get or create subjects
subject_instances = {}
for subject_name in ['Matematik', 'Geometri', 'Fizik', 'Kimya', 'Biyoloji', 'Türkçe', 'Edebiyat', 'Tarih', 'Coğrafya', 'Felsefe', 'Din Kültürü']:
    try:
        subject_instances[subject_name] = Subject.objects.get(name=subject_name)
    except Subject.DoesNotExist:
        print(f"Warning: Subject '{subject_name}' not found in database. Messages for this subject will be skipped.")

messages_data = {
    'Genel': {
        '0-20': [
            "Her şey bir adımla başlar! Önemli olan denemen, gerisi zamanla oturacak.",
            "Hatalar öğrenmenin bir parçasıdır. Şimdi nerede eksik olduğunu keşfedip ilerleyelim!",
            "Zorlandığın noktalar aslında gelişmeye en açık alanların. Sabırlı ol, başaracaksın!",
            "Öğrenmek zaman alır, kendine zaman tanı. Küçük ilerlemeler bile çok değerlidir!",
            "Şu an zor geliyor olabilir ama unutma, her yanlış seni doğruya bir adım daha yaklaştırır.",
            "Denemeye devam et! Azim ve kararlılıkla her şeyin üstesinden gelebilirsin.",
            "Başlangıçlar hep zordur, ama en büyük başarılar da küçük adımlarla başlar.",
            "Emin ol, bu seviyeden yükselmek sandığından çok daha kolay olacak!",
            "Öğrenme sürecindesin ve bu sürecin en değerli kısmı sabırla devam etmektir.",
            "Şimdi eksiklerini fark ettin, işte bu bile büyük bir adım! Haydi devam edelim!"
        ],
        '20-40': [
            "Başlangıcı yaptın, şimdi daha da güçlenme zamanı!",
            "Eksiklerini görmek, onları tamamlamanın ilk adımıdır. Devam et!",
            "Matematik, fizik veya tarih... Ne olursa olsun, tekrar ettikçe daha iyi anlayacaksın!",
            "İlerleme kaydediyorsun, bunu görmek harika! Daha fazla pratikle çok daha iyi olacaksın.",
            "Öğrenmenin en güzel yanı, her gün bir adım ileri gitmektir. Sen de bunu yapıyorsun!",
            "Bazı konular zorlayabilir ama pes etmezsen, kısa sürede farkı göreceksin!",
            "Şimdi eksiklerini belirleyip üzerine gidelim. Adım adım daha iyiye!",
            "Sen potansiyelinin farkında mısın? Biraz daha odaklanırsan harika işler çıkarabilirsin!",
            "Her soru, seni biraz daha geliştiriyor. Daha çok çöz, daha çok öğren!",
            "Çalışmalarının karşılığını almak için biraz daha sabır ve disiplin gerekiyor. Sen yapabilirsin!"
        ],
        '40-60': [
            "Tebrikler! Artık orta seviyeye geldin, bu harika bir gelişme!",
            "Temelleri oturttun, şimdi biraz daha sıkı çalışarak daha da ileriye gidebilirsin!",
            "Daha fazla pratik yaparak eksiklerini kapatabilir ve başarıyı yakalayabilirsin!",
            "Soruların neredeyse yarısını doğru yapıyorsun, devam edersen çok daha iyi olacaksın!",
            "Hatalarından ders çıkarmaya devam edersen, hızla yükselirsin!",
            "Başarıya bir adım daha yaklaştın, biraz daha çaba ile zirveye ulaşabilirsin!",
            "Bu seviyeye gelmek bile büyük bir başarı. Şimdi daha fazla test çözerek sağlamlaştır!",
            "Senin için her şey daha anlaşılır olmaya başladı, devam et!",
            "İlerleme kaydediyorsun, şimdi biraz daha sabır ve motivasyonla devam!",
            "Küçük adımlarla büyük farklar yaratabilirsin, az kaldı!"
        ],
        '60-80': [
            "Harikasın! Çoğu konuyu öğrenmişsin, ufak tefek eksikleri de tamamlayalım!",
            "İşin büyük kısmını hallettin, şimdi ustalaşma zamanı!",
            "Soruların çoğunu doğru yapıyorsun, bu harika! Daha da hızlanmak için çalışmaya devam et!",
            "Birkaç küçük dokunuşla çok daha iyi olabilirsin. Az kaldı, devam!",
            "Burası artık başarıya çok yakın olduğun nokta. Biraz daha çalış ve zirveye ulaş!",
            "Şimdiye kadar gösterdiğin çaba harika! Devam et, hedefe çok az kaldı!",
            "Artık işin püf noktalarını çözmeye başladın. Ufak tekrarlarla bilgileri pekiştirelim!",
            "Senin gibi kararlı biri için %80-%100 arası çok uzak değil. Biraz daha gayret!",
            "Testlerde daha yüksek netler yapabilmek için birkaç zorlu soruyla kendini test etmelisin!",
            "Bu seviyeye gelmek kolay değil! Şimdi biraz daha odaklanarak zirveye çıkma zamanı!"
        ],
        '80-100': [
            "Muhteşem bir iş çıkardın! Şimdi bilgilerini koruyarak bu seviyeyi sürdürelim!",
            "Artık ustalaştın! Şimdi daha fazla pratikle hız kazanma zamanı.",
            "Senin gibi azimli biri için başarı kaçınılmaz! Tebrikler, harika bir performans!",
            "Sınavda büyük başarı elde etmeye çok yakınsın, biraz daha tekrar yaparak hatasız hale gelebilirsin!",
            "Soruların büyük kısmını doğru çözdün, sadece birkaç ayrıntıya dikkat ederek tam puana ulaşabilirsin!",
            "Mükemmel! Artık kendini geliştirmek için daha zor sorularla kendini test edebilirsin.",
            "Bu noktaya gelmek için çok çalıştın ve emeğinin karşılığını alıyorsun. Gurur duymalısın!",
            "Her denemede kendini daha da geliştiriyorsun. Harikasın!",
            "Sen zaten başardın! Artık bilgilerini daha sağlamlaştırma ve tekrar yapma zamanı.",
            "Büyük hedefler koymaya devam et! Senin için sınır yok, hep daha iyisini yapabilirsin!"
        ]
    },
    'Matematik': {
        '0-20': [
            "Matematik zorlayıcı olabilir ama unutma, her şey temelden başlar. Önce dört işlem, sonra problemler!",
            "Matematik biraz sabır ister! İşlem hatalarına dikkat ederek yavaş yavaş ilerleyelim.",
            "Sayılarla aranı ısıtmak için bol bol işlem pratiği yapmalısın. Küçük adımlarla başlayalım!",
            "Önemli olan denemek! Matematiği anlamanın yolu, sabırla çözmeye devam etmekten geçiyor.",
            "Matematik öğrenmek kas geliştirmek gibidir, ne kadar çok çalışırsan o kadar güçlenirsin!"
        ],
        '20-40': [
            "Matematiğin temelini atıyorsun, şimdi kuralları iyice pekiştirme zamanı!",
            "Hata yapmaktan korkma! Eksiklerini tespit etmek, onları kapatmak için ilk adımdır.",
            "İşlem hızını artırmak için bol bol pratik yapmaya devam et!",
            "Problemler biraz zor gelebilir ama küçük ipuçlarını yakaladığında çözmek çok daha kolay olacak.",
            "Matematik bir bulmaca gibidir, sabırla çözersen sonunda tüm parçalar yerine oturacak!"
        ],
        '40-60': [
            "Orta seviyeye ulaştın! Şimdi zor problemlere daha fazla odaklanma zamanı.",
            "Eksik kaldığın konulara biraz daha yoğunlaşırsan çok daha iyi olacaksın!",
            "Matematikte hız kazanmak için bol bol soru çözmeye devam et!",
            "İşin büyük kısmını hallettin! Şimdi birkaç ekstra konu tekrarıyla çok daha ileriye gidebilirsin.",
            "Doğru sayın artıyor, süper gidiyorsun! Şimdi hatalarını analiz edip güçlenelim."
        ],
        '60-80': [
            "Süper gidiyorsun! Artık matematik konularına oldukça hakimsin.",
            "Karmaşık sorulara geçiş yapabilmek için işlem pratiğine biraz daha ağırlık verebilirsin.",
            "Çok güzel ilerliyorsun! Birkaç zorlu problemle kendini test etmeye ne dersin?",
            "Konuları kavradın, şimdi hız kazanma zamanı! Zaman tutarak test çözebilirsin.",
            "Öğrendiğin bilgileri farklı soru tiplerinde uygulayarak kendini daha da geliştirebilirsin."
        ],
        '80-100': [
            "Harikasın! Matematikte artık ustalaşma seviyesine geldin!",
            "Bu seviyeye gelmek kolay değil, emeğinin karşılığını alıyorsun!",
            "Artık en zor soruları bile çözebilecek durumdasın. Sınavda rahat ol, başaracaksın!",
            "Matematik senin için artık bir oyun gibi! Şimdi hızını artırarak tam puan hedefleyebilirsin.",
            "Bu kadar ilerlediysen, artık rakiplerinle değil kendinle yarışıyorsun! Hadi zirveye!"
        ]
    },
    'Geometri': {
        '0-20': [
            "Üçgenler, açılar, doğrular... Hepsi ilk başta zor gelebilir ama görselleştirerek çalışırsan çok daha kolay olacak!",
            "Şekilleri çizmeye ve ölçmeye alış! Görselleştirdikçe kavraman hızlanacak.",
            "Geometriyi anlamak için önce temel kuralları öğrenmek gerek. Açılarla başlayalım!",
            "Önce şekilleri tanımaya, sonra özelliklerini öğrenmeye odaklan. Sabırla devam et!",
            "Geometriyi oyun gibi düşün! Şekillerin içindeki ipuçlarını yakalarsan her şey kolaylaşır."
        ],
        '20-40': [
            "Temelleri atıyorsun, şimdi biraz daha şekillerin özelliklerini pekiştirelim!",
            "Hata yapmaktan korkma! Şekilleri çizmeye devam ettikçe daha iyi anlayacaksın.",
            "Üçgenler ve çemberler üzerine biraz daha yoğunlaşırsan farkı göreceksin!",
            "Birkaç ekstra örnek çözerek görsel hafızanı güçlendirebilirsin!",
            "Doğruları, açıları ve paralel kenarları birbirine karıştırmadan öğrenmeye odaklan!"
        ],
        '40-60': [
            "Şekillerle aranın iyi olduğu belli! Biraz daha çalışarak keskin bir geometri zekâsı kazanabilirsin.",
            "Açıları ve üçgenleri daha iyi kavradıkça geometri çok daha eğlenceli olacak!",
            "Yanlış yaptığın soruların mantığını öğrenerek ilerleyebilirsin.",
            "Biraz daha pratikle şekillerle arandaki bağı güçlendirebilirsin!",
            "Geometri soyut görünebilir ama bol soru çözdükçe gözünde canlanacak!"
        ],
        '60-80': [
            "Çok iyi gidiyorsun! Şimdi zor sorulara geçiş yapabilirsin.",
            "Özel üçgenler ve çemberlerle ilgili soruları artırmalısın!",
            "Geometriyi sezgisel olarak kavramaya başladın. Şimdi hız kazanmaya odaklan!",
            "Daha fazla deneme çözerek farklı soru tiplerine alışabilirsin.",
            "Artık kendini test etmek için önce zor soruları denemelisin!"
        ],
        '80-100': [
            "Mükemmel seviyeye geldin! Artık sadece sınav temposunu koruman yeterli!",
            "Üçgenlerden çemberlere, her konuda hakimsin! Şimdi hız ve zaman yönetimi çok önemli.",
            "Geometriyi çözmenin mantığını kavradın, artık sınav stratejilerini geliştirme vakti!",
            "Artık çözülmesi zor sorular seni korkutmuyor! Harika bir başarı!",
            "Son aşamada hızını artırıp hatalarını minimuma indirmelisin!"
        ]
    },
    'Fizik': {
        '0-20': [
            "Fizik zor mu geliyor? Unutma, bu formüller doğanın dili!",
            "Temel kavramları anlamadan ileriye geçme! Önce hareket ve kuvvet konularını pekiştir.",
            "Formülleri ezberleme, nasıl çalıştıklarını anlamaya çalış!",
            "Dersin içinde deneyler hayal ederek konuları daha iyi kavrayabilirsin!",
            "Newton bile bu noktadan başlamıştı! Sabırla devam et!"
        ],
        '20-40': [
            "İlerleme var! Şimdi biraz daha problem çözerek bilgini pekiştirebilirsin.",
            "Örnekler üzerinde çalışarak formülleri daha iyi anlayabilirsin.",
            "Kuvvet ve hareket konularına biraz daha yoğunlaş!",
            "Biraz daha pratik yaparsan fiziğin mantığını çok daha iyi anlayacaksın!",
            "Şimdi enerjini formülleri çözmeye harcayalım!"
        ],
        '40-60': [
            "Temel kavramları öğrendin! Şimdi biraz daha formüllerle pratik yapma zamanı.",
            "Soruların mantığını çözmeye başladın, şimdi hız kazanmaya odaklan!",
            "Yanlış yaptığın soruların çözümlerini detaylı inceleyerek ilerleyebilirsin.",
            "Fizikte görselleştirme çok önemli! Şemalar ve grafiklerle daha iyi öğrenebilirsin.",
            "Newton bile bu yolda zorlanmıştı! Sen de daha çok çalışarak geliştirebilirsin."
        ],
        '60-80': [
            "Çok iyi gidiyorsun! Şimdi konular arasındaki bağlantıları güçlendirmelisin.",
            "Zor sorulara geçiş yapabilirsin, fiziğin mantığını artık anladın!",
            "Deneme sınavlarında süre tutarak hızını test etmeye başla.",
            "Fizikteki formülleri ezberlemek yerine yorum yaparak çözmeye odaklan!",
            "Artık fizik senin için anlaşılır hale geldi! Hadi hızlan!"
        ],
        '80-100': [
            "Mükemmel! Artık sınav antrenmanı yaparak zirveye ulaşabilirsin!",
            "Fizikte uzmanlaştın! Şimdi hız ve dikkat üzerine çalışmalısın.",
            "Sınav öncesi tekrarlarını planlı yaparak bilgilerini pekiştir!",
            "Formüller artık senin için birer araç, doğru zamanda doğru kullanmalısın!",
            "Fizikteki başarın seni sınavın en zor sorularına bile hazır hale getirdi!"
        ]
    },
    'Kimya': {
        '0-20': [
            "Kimya formüllerden ibaret değil! Önce temel kavramları anlamaya odaklanalım.",
            "Atomlar, elementler... Başta karışık gibi görünebilir ama adım adım ilerlediğinde her şey yerine oturacak!",
            "Deney yapıyormuş gibi düşün! Kimya, hayatın her alanında var.",
            "Önce periyodik tabloyu tanımaya ne dersin? Elementleri öğrendikçe işin kolaylaşacak!",
            "Kimyayı bir bulmaca gibi gör! Küçük parçaları birleştirdiğinde büyük resmi göreceksin."
        ],
        '20-40': [
            "Bağları güçlendirme zamanı! Atomların nasıl birleştiğini iyice kavrayalım.",
            "Formülleri ezberlemek yerine mantığını kavramaya odaklan!",
            "Kimyasal tepkimeleri bol bol tekrar edersen daha akılda kalıcı hale gelecektir.",
            "Birkaç deney videosu izleyerek konulara farklı bir bakış açısı kazandırabilirsin!",
            "Asit-baz dengelerini anlamak için örnekler çözmeye devam et!"
        ],
        '40-60': [
            "Atomlar arasındaki bağları çözmeye başladın! Şimdi biraz daha detaylara inelim.",
            "Kimyanın dili formüllerdir! Biraz daha pratikle onları daha iyi anlayabilirsin.",
            "Eksik olduğun konuların üzerinden geçerek bilgilerini pekiştirebilirsin!",
            "Tepkimeleri ve denklemleri bol bol yazarak çalışmak akılda kalıcılığı artırır!",
            "Maddenin halleri, çözünürlük ve asit-baz konularına daha fazla vakit ayırarak gelişebilirsin!"
        ],
        '60-80': [
            "Harika bir seviyeye ulaştın! Şimdi zor sorulara odaklanmalısın.",
            "Kimyasal denklemleri ezberlemek yerine mantığını kavramaya çalış!",
            "Zor konulara daha fazla yoğunlaşarak eksiklerini kapatabilirsin.",
            "Kimya problemlerinde hız kazanmak için bol bol deneme çözmelisin!",
            "Artık yorum gerektiren sorulara daha rahat yaklaşabiliyorsun, devam et!"
        ],
        '80-100': [
            "Mükemmel bir noktadasın! Artık kimyada ustalaştın!",
            "Zor sorular seni artık korkutmuyor! Sınav anında hızlı ve dikkatli olmalısın.",
            "Kimyanın püf noktalarını kavradın, şimdi test stratejilerine odaklanabilirsin!",
            "Artık ince detaylara odaklanarak fark yaratma zamanı!",
            "Kimyasal denklemleri, tepkimeleri ve çözümleri hızlıca yorumlayabiliyorsun. Harika!"
        ]
    },
    'Biyoloji': {
        '0-20': [
            "Biyoloji ezber gibi görünebilir ama aslında mantığı çok sağlam! Canlıların yapı taşlarını anlamaya başlayalım.",
            "Hücreleri tanımadan biyolojiyi öğrenmek zor olur. Önce temel yapı taşlarını kavrayalım!",
            "Organizmaların nasıl çalıştığını anlamak için şemalar ve görseller kullanabilirsin.",
            "Biyoloji her yerde! Günlük hayatındaki örnekleri düşünerek çalışmak öğrenmeni hızlandırır.",
            "Hayvanlar, bitkiler ve mikroorganizmalar... Hepsi bir sistemin parçası! Büyük resmi görmeye odaklan."
        ],
        '20-40': [
            "Temelleri öğrendikçe bilgiler daha anlamlı hale gelecek. Hadi hücrelerden başlayalım!",
            "Canlıların işleyişini anlamak için grafikler ve tablolar oluşturabilirsin!",
            "Görsellerle çalışmak biyolojiyi anlamanı kolaylaştırır. Konu anlatımlı kaynakları inceleyebilirsin.",
            "Biraz daha detaylara inerek organ sistemlerini kavramaya başlayalım!",
            "Biyolojiyi öğrenmenin en iyi yolu, doğaya gözlerini açmak! Çevrendeki canlıları inceleyerek öğrenmeye devam et."
        ],
        '40-60': [
            "Canlıların dünyasına giriş yaptın! Şimdi detayları öğrenme vakti.",
            "Biyoloji ezber gibi görünebilir ama aslında bir mantık var! Konular arasındaki bağlantıları kurmalısın.",
            "Hücre, organeller ve sistemler konularında eksiklerini tamamlamaya odaklan!",
            "Biyolojide görsel çalışmak çok önemli! Çizimler ve tablolarla çalışmayı dene.",
            "Konuları hikayeleştirerek veya kısa notlarla pekiştirerek daha kalıcı öğrenebilirsin!"
        ],
        '60-80': [
            "Harika gidiyorsun! Şimdi detaylı bilgilerle kendini geliştir!",
            "Biyoloji sorularında dikkat hatalarını azaltmak için bol pratik yapmalısın.",
            "Canlılar arasındaki benzerlikleri ve farklılıkları öğrenmek seni çok ileri taşıyacak!",
            "Sınavda sorular daha çok yorum gerektirecek, o yüzden detaylara biraz daha odaklanmalısın!",
            "Zor konulara (sinir sistemi, genetik vb.) odaklanarak eksiklerini giderebilirsin!"
        ],
        '80-100': [
            "Mükemmel bir seviyedesin! Artık en karmaşık biyoloji sorularını bile çözebilirsin!",
            "Sınavda zaman kazandıracak kısayolları öğrenerek fark yaratabilirsin!",
            "Şimdi deneme çözüp hatalarını analiz ederek hızını artırma zamanı!",
            "Biyolojide artık uzmanlık seviyesine ulaştın, tekrarlarını düzenli yapmaya devam et!",
            "Bilgilerini sınava kadar taze tutarak biyoloji senin en güçlü derslerinden biri olabilir!"
        ]
    },
    'Türkçe': {
        '0-20': [
            "Dil bilgisi biraz teknik olabilir ama adım adım ilerleyerek tüm kuralları kolayca öğrenebilirsin!",
            "Paragraf sorularında zorlanıyorsan, bol bol okuma yaparak anlama hızını artırabilirsin.",
            "Noktalama işaretleri ve yazım kurallarına odaklanarak eksiklerini kapatmaya başlayalım!",
            "Kelime dağarcığını geliştirmek için her gün yeni kelimeler öğrenmeye ne dersin?",
            "Türkçede başarılı olmanın sırrı dikkatli okumak ve mantık yürütmek! Hadi pratik yapalım."
        ],
        '20-40': [
            "Paragraf sorularında dikkatini artırarak daha iyi sonuçlar alabilirsin!",
            "Dil bilgisi konularını küçük parçalar halinde öğrenmek işini kolaylaştırır.",
            "Soruları çözerken acele etme, özellikle uzun paragraflarda odaklanmaya çalış!",
            "Paragraf sorularında önce soru kökünü dikkatlice okumak büyük fark yaratır!",
            "Türkçede başarı için en iyi yol bol bol soru çözmek ve yanlışlarından ders çıkarmak!"
        ],
        '40-60': [
            "Güzel bir seviyeye ulaştın! Şimdi hız ve doğruluk üzerine çalışmalısın.",
            "Paragraflarda okuma hızını artırmak için her gün birkaç metin okumayı deneyebilirsin.",
            "Dil bilgisi kurallarını örneklerle pekiştirmek daha iyi kavramanı sağlar!",
            "Bağlaçlar, fiilimsiler ve anlatım bozuklukları gibi konulara biraz daha odaklanmalısın.",
            "Sorularda doğru seçenekleri eleyerek ilerlemek işini kolaylaştıracaktır!"
        ],
        '60-80': [
            "Harika gidiyorsun! Paragraf sorularında hızını artırarak daha iyi sonuçlar alabilirsin.",
            "Çeldiricilere dikkat! Özellikle benzer seçenekleri iyi analiz etmelisin.",
            "Dil bilgisi konularında tekrar yaparak bilgilerini daha da sağlamlaştırabilirsin!",
            "Anlam bilgisi sorularında daha hızlı olmak için her gün kısa metinler okuyabilirsin.",
            "Test çözerken hata yaptığın konuların üzerinden geçerek eksiklerini tamamla!"
        ],
        '80-100': [
            "Mükemmel bir noktadasın! Artık Türkçede uzmanlaşmak için hız ve dikkat odaklı çalışmalısın.",
            "Son aşamada zorlayıcı denemeler çözerek sınav ortamına hazırlanabilirsin!",
            "Dil bilgisi ve paragraf sorularında hatasız olabilmek için analizlerini dikkatlice yapmalısın.",
            "Paragraf sorularını daha hızlı çözerek zaman yönetimini mükemmelleştirebilirsin!",
            "Bu seviyede, en küçük detayları bile gözden kaçırmamak için dikkatini en üst seviyeye çıkarmalısın!"
        ]
    },
    'Edebiyat': {
        '0-20': [
            "Şairler ve yazarlar başta karışık gelebilir ama akılda tutmanın yolu hikayeler oluşturmaktan geçer!",
            "Edebiyat, geçmişi anlamanın en güzel yollarından biridir. Yazarların hayat hikayelerine göz atmak işini kolaylaştırabilir!",
            "Eserleri, dönemleriyle birlikte öğrenirsen daha kalıcı olur. Tarih ve edebiyatı birlikte çalışmayı dene!",
            "Belli başlı edebi akımları öğrendiğinde eserleri çok daha kolay hatırlayabilirsin.",
            "Şiir ezberlemek gözünü korkutmasın! Kafiyeler ve ritim sayesinde daha akılda kalıcı hale gelir."
        ],
        '20-40': [
            "Edebiyat bilgisi birikimle gelişir! Konuları kısa özetlerle çalışarak öğrenmeye devam et.",
            "Şair ve yazar isimleri, eserler ve akımlar karışıyor olabilir, ama tekrar yaparak zihninde oturtabilirsin!",
            "Eser özetlerini okuyarak hikâyeleri aklında daha iyi tutabilirsin!",
            "Edebiyat sorularında anahtar kelimelere odaklanarak yanlışlarını azaltabilirsin!",
            "Öğrendiğin bilgileri testlerle pekiştirmek hafızanı güçlendirecektir!"
        ],
        '40-60': [
            "Şair ve yazarlar aklında yer etmeye başladı! Şimdi detaylara odaklanma zamanı.",
            "Edebî akımları ve dönemleri tablolar hâlinde çalışarak daha iyi öğrenebilirsin!",
            "Sık yapılan hataları analiz ederek gelişimini hızlandırabilirsin!",
            "Şiir ve roman türlerindeki farkları öğrenmek için örnek eserlerden yararlanabilirsin.",
            "Edebi sanatlar ve terimleri ezberlemek yerine bol örnekle çalışarak pekiştirebilirsin!"
        ],
        '60-80': [
            "Çok iyi gidiyorsun! Eserleri ve yazarları artık büyük ölçüde tanıyorsun!",
            "Zor edebiyat sorularında seçenekleri dikkatli eleyerek doğruya ulaşabilirsin.",
            "Eserleri ve yazarları hikâyelerle bağdaştırarak öğrenmek hatırlamanı kolaylaştırır.",
            "Farklı soru tipleri çözerek sınavdaki tüm sürprizlere hazırlıklı olabilirsin!",
            "Deneme sınavlarında edebiyat netlerini artırmak için eksik kaldığın konulara yoğunlaşmalısın!"
        ],
        '80-100': [
            "Edebiyatı artık ustalık seviyesinde çözüyorsun! Detaylı analizlerle en iyi sonucu alabilirsin.",
            "Son aşamada deneme çözerek bilgilerini pekiştirmeye devam et!",
            "Artık şairlerin ve yazarların üslubunu dahi fark edebilirsin, bu büyük bir avantaj!",
            "Eserleri sadece isim olarak değil, konularını da hatırlayarak sınavda fark yaratabilirsin!",
            "Son düzlüğe girdin, şimdi hız ve dikkat konusuna odaklanarak mükemmel bir sonuç alabilirsin!"
        ]
    },
    'Tarih': {
        '0-20': [
            "Tarih sayılardan ibaret değil! Olaylar arasındaki bağlantıyı kurarsan her şey daha anlamlı hale gelir.",
            "Padişahları, savaşları ve antlaşmaları ezberlemek yerine hikayeler oluşturarak öğrenmeyi dene!",
            "Tarih akılda kalıcıdır, çünkü yaşanmış olaylardan oluşur. Olayları sırasıyla düşünerek öğrenmeye çalış!",
            "Kronolojik sıralama yaparak çalışmak işini kolaylaştırabilir!",
            "Tarihi anlamak için neden-sonuç ilişkisini iyi kavramak gerekir. Hadi birkaç örnekle alıştırma yapalım!"
        ],
        '20-40': [
            "Tarih, olaylar arasındaki bağlantıları görmekle öğrenilir! Kronolojik sıraya dikkat ederek çalışmaya devam et.",
            "Tarihi ezberlemek yerine, neden-sonuç ilişkilerini anlamaya çalışarak daha kalıcı öğrenebilirsin!",
            "Önemli savaşlar, antlaşmalar ve liderler konusunda özet çıkararak çalışmak işini kolaylaştırabilir.",
            "Tarih sorularında dikkat hatalarını azaltmak için anahtar kelimelere odaklan!",
            "Konuların üzerinden tekrar geçerek eksik noktalarını tamamlamaya devam et, başarıya çok yaklaşıyorsun!"
        ],
        '40-60': [
            "Olaylar arasındaki bağlantıyı kuruyorsun! Şimdi detaylara biraz daha odaklanma vakti.",
            "Kronolojik çalışarak daha hızlı hatırlayabilirsin!",
            "Hikaye gibi öğrenmeye devam et! Bu şekilde bilgiler kalıcı olacak.",
            "Daha fazla deneme çözerek eksiklerini belirleyebilirsin.",
            "Önemli savaşları ve antlaşmaları öğrenirken neden-sonuç ilişkisini kurmalısın!"
        ],
        '60-80': [
            "Tarih bilgin çok iyi! Şimdi ince detaylara odaklanarak geliştirebilirsin.",
            "Önemli olayların yıllarını daha iyi hatırlamak için kodlamalar yapabilirsin.",
            "Konuların bağlantılarını kurarak bütüncül bir bakış açısı kazanmalısın!",
            "Tarihi hatırlamanın en iyi yolu bol tekrar! Şimdi biraz daha çalışalım.",
            "Artık tarih kitaplarına farklı bir gözle bakıyorsun! Harika ilerleme!"
        ],
        '80-100': [
            "Mükemmel! Artık tarihte ustalaştın, sadece sınav antrenmanı yapman yeterli!",
            "Özet çıkararak ya da haritalarla çalışarak bilgilerini daha da pekiştirebilirsin.",
            "Artık zor tarih sorularında bile rahatlıkla yorum yapabiliyorsun!",
            "Tarih sorularında hız ve dikkat üzerine yoğunlaşmalısın!",
            "Harika bir seviyeye geldin! Şimdi en zor soruları bile çözebilirsin."
        ]
    },
    'Coğrafya': {
        '0-20': [
            "Haritalarla çalışmak coğrafyayı anlamanı kolaylaştırır. Dünya üzerindeki yerleri gözünde canlandır!",
            "İklim tiplerini ve yer şekillerini öğrenerek coğrafyanın temelini atabilirsin.",
            "Bir bölgenin özelliklerini öğrenirken o bölgeye ait fotoğraflar incelemek akılda kalıcılığı artırır.",
            "Harita okumayı öğrenmek coğrafyada başarılı olmanın anahtarıdır. Başlangıç için mükemmel bir yerdesin!",
            "Coğrafyada grafik ve tabloları okumayı öğrenmek işini çok kolaylaştıracaktır."
        ],
        '20-40': [
            "Haritalarla çalışarak görselleştirme yap, konular aklında daha iyi kalır!",
            "İklim tipleri, yer şekilleri gibi konuları grafik ve şemalarla öğrenmek işini kolaylaştırır.",
            "Coğrafyada ezber yapmak yerine, mantığını anlamaya çalışarak öğrenmek daha kalıcıdır!",
            "Yanlış yaptığın soruların konularına odaklanarak eksiklerini belirleyebilirsin.",
            "Yer şekillerini, göller ve akarsuları öğrenirken haritalara sık sık bakmayı ihmal etme!"
        ],
        '40-60': [
            "Coğrafya çalışırken görsel materyaller kullanmak bilgiyi daha iyi pekiştirmeni sağlar!",
            "İklim ve bitki örtüsü konularında karşılaştırmalar yaparak benzerlikleri ve farkları anlamaya çalış!",
            "Harita okuma becerilerini geliştirmek için bol bol harita sorusu çözmelisin!",
            "Sınavlarda sık çıkan konulara odaklanarak çalışmalarını daha verimli hâle getirebilirsin.",
            "Çıkmış sorulara göz atarak soru tarzlarını daha iyi kavrayabilirsin!"
        ],
        '60-80': [
            "Çok iyi ilerliyorsun! Şimdi detaylara odaklanarak netlerini artırabilirsin.",
            "Soruların çoğunu yapabiliyorsun, ancak dikkat hatalarına karşı daha temkinli olmalısın.",
            "Fiziki, beşeri ve ekonomik coğrafya konularında eksik kaldığın noktaları belirleyerek tamamla!",
            "Harita üzerinden çalışarak yer şekilleri ve iklim kuşaklarını daha iyi pekiştirebilirsin.",
            "Şimdi biraz daha hızlanarak ve daha fazla deneme çözerek kendini test etme zamanı!"
        ],
        '80-100': [
            "Mükemmel gidiyorsun! Coğrafyada artık uzman seviyesine ulaştın!",
            "Son aşamada hız ve dikkat konularına odaklanarak soruları daha hızlı çözebilirsin!",
            "Bütün konuları öğrendin, şimdi deneme sınavlarıyla bilgilerini test etmeye devam et!",
            "Coğrafya sorularında hatasız olabilmek için detaylara biraz daha dikkat etmelisin.",
            "Harika bir seviyeye ulaştın, son olarak zaman yönetimi ve hız konularına odaklanmalısın!"
        ]
    },
    'Felsefe': {
        '0-20': [
            "Felsefe düşünmeyi öğretir! Önce temel kavramlarla başlamaya ne dersin?",
            "Felsefi akımları öğrenmek için farklı filozofların görüşlerini karşılaştırarak çalışabilirsin.",
            "Sorulara farklı açılardan bakarak düşünme becerini geliştirebilirsin!",
            "Felsefede önemli olan doğru cevabı bulmak değil, düşünmeyi öğrenmektir!",
            "Felsefe biraz sabır ister, düşünmeye zaman tanı!"
        ],
        '20-40': [
            "Felsefeyi anlamanın en iyi yolu, filozofların temel sorularını kavramaktır. Onların neyi sorguladığını keşfetmeye çalış!",
            "Ezber yapmaktan çok, farklı filozofların düşünce yapılarını karşılaştırarak öğrenmek daha kalıcı olur!",
            "Metin sorularında anahtar kelimeleri belirleyerek düşünce akışını daha iyi anlayabilirsin.",
            "Felsefe konularını bir hikâye gibi okuyarak olaylar arasındaki bağlantıları kurmaya çalış!",
            "Yanlış yaptığın soruları analiz edip, aynı konuyla ilgili başka sorular çözerek eksiklerini giderebilirsin!"
        ],
        '40-60': [
            "Filozofların görüşlerini öğrenmeye başladın! Şimdi aralarındaki farkları anlamaya odaklan!",
            "Düşünce akımlarını karşılaştırmalı tablolarla çalışarak bilgini pekiştirebilirsin!",
            "Metin yorumlama sorularında, verilen düşüncenin hangi akıma veya filozofa ait olabileceğini düşünerek analiz yap!",
            "Önemli filozofların eserlerini ve ana görüşlerini kavramaya başladın, şimdi detaylara inme zamanı!",
            "Kavramları birbiriyle ilişkilendirerek çalışırsan felsefeyi daha kolay öğrenebilirsin!"
        ],
        '60-80': [
            "Felsefe bilgini iyice oturtmuşsun! Şimdi yorum yapma becerini geliştirerek netlerini artırabilirsin.",
            "Önemli filozofların temel düşüncelerini birbiriyle kıyaslayarak daha güçlü bir analiz yapabilirsin!",
            "Soyut kavramları somut örneklerle destekleyerek çalışmak, bilgini kalıcı hâle getirecektir.",
            "Soru çözümlerinde dikkat hatalarını azaltarak daha yüksek doğruluk oranı yakalayabilirsin!",
            "Artık metin sorularında filozofların bakış açılarını hızla fark edebiliyorsun, harika bir gelişim gösterdin!"
        ],
        '80-100': [
            "Felsefede uzmanlaştın! Artık filozofların düşüncelerini metinden kolayca çıkarabiliyorsun.",
            "Son aşamada hız ve dikkat konularına odaklanarak mükemmel sonucu alabilirsin!",
            "Önemli felsefi akımları, temel ilkelerini bilerek yorumlamak seni sınavda bir adım öne taşıyacaktır!",
            "Şimdi bol bol deneme çözerek son rötuşları yap ve kendini test etmeye devam et!",
            "Sınavda tüm filozofları tanıyacak ve sorulara güvenle yaklaşacaksın! Tebrikler, harika bir seviyeye ulaştın!"
        ]
    },
    'Din Kültürü': {
        '0-20': [
            "Dinler tarihi ve temel kavramları öğrenmek, dünyayı daha iyi anlamanı sağlar!",
            "Kavramları anlamak için günlük hayattan örnekler bulmaya çalış!",
            "Farklı inanç sistemlerini öğrenerek konuya geniş bir bakış açısı kazandırabilirsin.",
            "Terimleri ve kavramları öğrenirken onları açıklamaya çalışmak akılda kalıcılığı artırır.",
            "İnanç, ahlak ve kültürün iç içe geçtiği bu ders için önce temel bilgileri oturtalım!"
        ],
        '20-40': [
            "Dini kavramları öğrenirken anahtar kelimelere dikkat et, böylece konuları daha iyi hatırlayabilirsin!",
            "İslam'ın temel esaslarını, iman ve ibadetle ilgili bilgileri özet çıkararak çalışmak işini kolaylaştırır.",
            "Kavramları günlük hayattan örneklerle ilişkilendirerek öğrenmeye çalış, daha kalıcı olacaktır!",
            "Yanlış yaptığın soruların konularını belirleyerek eksiklerini tamamlamaya odaklan!",
            "Dinler ve ahlaki değerler konularında karşılaştırmalar yaparak farkları daha iyi anlayabilirsin!"
        ],
        '40-60': [
            "Temel dini bilgiler konusunda iyi bir seviyeye geldin, şimdi biraz daha detaylara odaklanmalısın!",
            "İslam ahlakı ve ibadetleriyle ilgili bilgileri anlamlandırarak öğrenmek, sınavda hız kazandıracaktır!",
            "Peygamberlerin hayatlarını, vahiy sürecini ve temel kavramları birbiriyle ilişkilendirerek öğren!",
            "Sık yapılan dikkat hatalarına karşı daha dikkatli olmalısın, özellikle kavram sorularında!",
            "Çıkmış sorulara göz atarak soru tarzlarını kavramaya çalış, büyük faydasını göreceksin!"
        ],
        '60-80': [
            "Çok iyi ilerliyorsun! Şimdi bilgilerini derinleştirerek konular arasındaki bağlantıları güçlendirebilirsin.",
            "Dini metinleri anlamlandırarak okumaya devam et, yorum yeteneğini geliştirmek için bu çok önemli!",
            "Soruların çoğunu doğru yapıyorsun, ancak dikkat hatalarını azaltmak için biraz daha pratik yapabilirsin!",
            "İslam'ın temel esasları, mezhepler ve farklı inanç sistemleri konusunda detayları öğrenmeye odaklan!",
            "Bol bol test çözerek öğrendiklerini pekiştirilebilir, yanlış yaptığın konulara tekrar dönebilirsin!"
        ],
        '80-100': [
            "Harika bir seviyeye ulaştın! Artık sınavda en ufak hatayı bile yapmamak için dikkatli olmalısın!",
            "Soruları analiz etme ve yorumlama becerin oldukça gelişti, şimdi hızını artırmaya odaklan!",
            "Öğrendiklerini pekiştirmek için son tekrarlarını yap ve kendini deneme sınavlarıyla test et!",
            "Zaman yönetimini iyi kullanarak soruları daha hızlı çözebilir ve eksiksiz bir performans sergileyebilirsin!",
            "Bu başarıyı hak ettin! Artık konulara tam anlamıyla hâkimsin, sınavda bunu göstermek için hazırsın!"
        ]
    }
}

for subject_name, ranges in messages_data.items():
    for range_key, messages in ranges.items():
        range_id = range_mapping.get(range_key)
        if not range_id:
            print(f"Warning: Invalid range key '{range_key}'. Skipping.")
            continue

        for message in messages:
            if subject_name == 'General':
                # For general messages, set subject to None
                MotivationalMessage.objects.create(
                    success_rate_range=range_id,
                    subject=None,
                    message=message,
                    is_active=True
                )
            elif subject_name in subject_instances:
                # For subject-specific messages, use the subject instance
                MotivationalMessage.objects.create(
                    success_rate_range=range_id,
                    subject=subject_instances[subject_name],
                    message=message,
                    is_active=True
                )
            else:
                print(f"Skipping message for subject '{subject_name}' as it was not found.")

print("Motivational messages imported successfully!")