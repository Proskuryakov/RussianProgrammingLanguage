
.class                   public Main
.super                   java/lang/Object

.method                  public <init>()V
   .limit stack          1
   .limit locals         1
   .line                 2
   aload_0               
   invokespecial         java/lang/Object/<init>()V
   return                
.end method     
  .method public static func_0(II)I
    .limit stack 8
    .limit locals 2

	iload				0
	iload				1
	iadd
	ireturn

.end method


  .method public static main([Ljava/lang/String;)V
    .limit stack 8
    .limit locals 4

	ldc				3
	istore				0
	ldc				2
	istore				1
	iload				0
	ldc				110
	invokestatic				Main/func_0(II)I
	istore				2
	iload				0
	iload				1
	iadd
	iload				2
	iadd
	istore				3
	getstatic java/lang/System/out Ljava/io/PrintStream;
	iload				3
invokevirtual java/io/PrintStream/println(I)V

return

.end method


