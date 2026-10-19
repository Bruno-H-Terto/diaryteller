# Retrofit and kotlinx.serialization keep their generic signatures.
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** { kotlinx.serialization.KSerializer serializer(...); }
