from algopy import ARC4Contract, arc4,UInt64, urange,ensure_budget,OpUpFeeSource,LocalState, Txn,OnCompleteAction,StateTotals,Bytes,GlobalState,Account
from algopy.arc4 import abimethod,String

SCALE = 10000  # 3 decimal fixed-point scale
LN2_FP = 6931   # ln(2) * SCALE ≈ 0.6931 * 10000

class SCReviewerSelectionFinalv6(
    ARC4Contract,
    state_totals=StateTotals(global_uints=50)
    ):
    def __init__(self)->None:
        self.vl_tl_diff = LocalState(UInt64)
        self.va = LocalState(UInt64)
        self.nak= LocalState(UInt64)
        self.klsimi=LocalState(UInt64)
        self.sstatus=LocalState(UInt64)

    #@abimethod(allow_actions=OnCompleteAction.OptIn)
    @abimethod(allow_actions=['OptIn'])
    def opt_in(self) -> None:
        # Initialize the number for the account
        self.vl_tl_diff[Txn.sender] = UInt64(0)
        self.va[Txn.sender] = UInt64(0)
        self.nak[Txn.sender]= UInt64(0)
        self.klsimi[Txn.sender]=UInt64(0)
        self.sstatus[Txn.sender]=UInt64(0)
    #i need to remove sstatu whiel writing by reviewer.
    @abimethod()
    def write_number(self,vl_tl_diff: UInt64,va:UInt64,nak:UInt64,klsimi:UInt64) -> UInt64:
        # Allow the sender to write a UInt64 number to their own local storage
        self.vl_tl_diff[Txn.sender] = vl_tl_diff
        self.va[Txn.sender] = va
        self.nak[Txn.sender]= nak
        self.klsimi[Txn.sender]=klsimi
        self.sstatus[Txn.sender]=UInt64(0)
        return UInt64(1)
    ## selection of top 3 Reviewers for the reviewing task.
    @abimethod()
    def selection(self,account1:Account, account2:Account, account3:Account,account4:Account) -> UInt64:
        # Allow the sender to write a UInt64 number to their own local storage
        self.sstatus[account1] = UInt64(1)
        self.sstatus[account2] = UInt64(1)
        self.sstatus[account3]= UInt64(1)
        self.sstatus[account4]= UInt64(1)
        return UInt64(1)
    @abimethod()
    def read_number(self,account:Account) -> tuple[UInt64,UInt64,UInt64,UInt64,UInt64]:
        # Anyone can read the number stored for a given account
        return (
            self.vl_tl_diff[account],
            self.va[account],
            self.nak[account],
            self.klsimi[account],
            self.sstatus[account])
    @arc4.abimethod()
    def fp_add(self, a: UInt64, b: UInt64) -> UInt64:
        """
        Fixed-point addition: (a + b)
        """
        return a + b

    @arc4.abimethod()
    def fp_sub(self, a: UInt64, b: UInt64) -> UInt64:
        """
        Fixed-point subtraction: (a - b)
        """
        if(a>b):
            return a - b  # Assumes a >= b
        else:
            return b - a

    @arc4.abimethod()
    def fp_mul(self, a: UInt64, b: UInt64) -> UInt64:
        """
        Fixed-point multiplication: (a * b) / SCALE , SCALE=1000
        """
        SCALE=UInt64(SCALE)
        return (a * b)//SCALE

    @arc4.abimethod()
    def fp_div(self, a: UInt64, b: UInt64) -> UInt64:
        """
        Fixed-point division: (a / b) = (a * SCALE) / b
        """
        SCALE=UInt64(SCALE)
        return (a * SCALE)//b
    @arc4.abimethod
    def set_key_value(self,account:Account, value: UInt64) -> None:
        """
        Dynamically sets a global key-value pair.
        Key and value must be bytes (can encode strings or numbers as bytes).
        """
        state = GlobalState(UInt64, key=account.bytes)
        state.value = value

    @arc4.abimethod
    def get_value(self,) -> UInt64:
        """
        Retrieves a value from global state by key.
        """
        state = GlobalState(UInt64, key=Txn.sender.bytes)
        return state.value
    @arc4.abimethod()
    def expo(self, g: UInt64, terms: UInt64) -> UInt64:
        """
        Approximate 2^g using Taylor series and fixed-point:
          2^g ≈ sum_{n=0}^{terms-1} ((g * ln2)^n / n!) in scaled form.
        g and result are fixed-point (×1000). 'terms' is loop count.
        """
        ensure_budget(2100)
        SCALE=UInt64(SCALE)
        #LN2_FP = UInt64(LN2_FP)
        term = SCALE
        result = UInt64(0)
        #assert result == 0, "Intial result initial not 0"
        
        fact = UInt64(1)
        fact=fact*SCALE 
        #assert fact==SCALE,"fact error"
        for n_int in urange(1, terms+1):
            n = n_int
            term1 = g
            if(n==1):
                term=SCALE
                term_div=self.fp_div(term,fact)
            elif(n==2):
                term=term1
                term_div=self.fp_div(term,fact)
            else:
                term=self.fp_mul(term1,term)
                nf=(n-1)*SCALE #NP representation of n value
                fact=self.fp_mul(fact,nf)
                term_div=self.fp_div(term,fact)
            result = result + term_div
        #print(f"result: {result}")
        return result
    @arc4.abimethod()
    def exp2(self, g: UInt64, terms: UInt64) -> UInt64:
        """
        Approximate 2^g using Taylor series and fixed-point:
          2^g ≈ sum_{n=0}^{terms-1} ((g * ln2)^n / n!) in scaled form.
        g and result are fixed-point (×1000). 'terms' is loop count.
        """
        ensure_budget(2100)
        SCALE=UInt64(SCALE)
        LN2_FP = UInt64(LN2_FP)
        term = SCALE
        result = UInt64(0)
        #assert result == 0, "Intial result initial not 0"
        
        fact = UInt64(1)
        fact=fact*SCALE 
        #assert fact==SCALE,"fact error"
        for n_int in urange(1, terms+1):
            n = n_int
            term1 = self.fp_mul(g,LN2_FP)
            if(n==1):
                term=SCALE
                term_div=self.fp_div(term,fact)
            elif(n==2):
                term=term1
                term_div=self.fp_div(term,fact)
            else:
                term=self.fp_mul(term1,term)
                nf=(n-1)*SCALE #NP representation of n value
                fact=self.fp_mul(fact,nf)
                term_div=self.fp_div(term,fact)
            result = result + term_div
        #print(f"result: {result}")
        return result

    @arc4.abimethod()
    def approx_log2(self, n_scaled: UInt64) -> UInt64:
        """
        Ensure Budget is set with 2000 and Souce is given.
        """
        ensure_budget(2000,OpUpFeeSource.AppAccount)
        SCALE=UInt64(SCALE)
        LN2_FP = UInt64(LN2_FP)
        g=UInt64(15000)
        n_scaled = self.fp_div(UInt64(10000),n_scaled)
        num = UInt64(10000)
        while(num>UInt64(100)):
            """
            Approximate log base 2 of a scaled integer `n` using Newton's method.
            `g` is the initial guess, both in fixed-point.
            Returns the next approximation, also fixed-point v2 with 3 decimals and single return value LN2_FP as 3 decimla 693.
            """
    
            # ---- Step 1: Compute 2^g ----
            # We approximate 2^g using: 2^g ≈ exp(g * ln(2))

    
            two_pow_g = self.exp2(g,UInt64(8)) #initial g value, and number of tylor series terms.
            
            numerator = self.fp_sub(two_pow_g,n_scaled)
            denominator=self.fp_mul(two_pow_g,LN2_FP)
           
            correction = self.fp_div(numerator,denominator)    #one_minus * SCALE // LN2_FP  # correction term in fixed point
    
            # ---- Step 3: Compute new approximation ----
            g_next = self.fp_sub(g,correction)#g - correction  # g - correction
            #print(f"g and corrections and y next :{g},{correction},{g_next}")
            num=self.fp_sub(g,g_next)
            g=g_next
            #print(f"num value for the next while loop {num}")    
        return g_next
    @arc4.abimethod()
    def InvRva(self, R_va_scaled: UInt64) -> UInt64:
        """
            (1-R_va)^-2 result are in FP
        """
        #SCALE=UInt64(SCALE)
        SCALE=UInt64(SCALE)
        InR_va=self.fp_sub(SCALE,R_va_scaled)
        #InR_va=self.fp_mul(InR_va,InR_va)
        result=self.fp_div(SCALE,InR_va)
        return result
    @arc4.abimethod()
    def area(self, R_va_scaled: UInt64,R_ak_scaled:UInt64) -> UInt64:
        """
        This is take validation accuracy(R_va) and Normalized area(R_ak/k) and calculate k*R_va/R_ak
        """
        SCALE=UInt64(SCALE)
        R_ak_inver = self.fp_div(SCALE,R_ak_scaled)
        result=self.fp_mul(R_ak_inver,R_va_scaled)
        result=self.fp_mul(result,self.expo(2*R_va_scaled,UInt64(8)))
        return result
    @arc4.abimethod()
    def Mperformance(self,account1:Account)->tuple[UInt64,UInt64,UInt64,UInt64]:
        """
        Proposed function to assign the relevance score to each model, to select it for reviewing task.
        R_mp=-log2(|R_vl-Rtl|) * (1-R_va)^-2 +k*R_va/R_ak
        R_dsg= R_dsg , given as input after offline calculation
        mp,Rscore= R_mp+R_dsg , mp= model performance score and final relevance score.
        """
        Nlog=self.approx_log2(self.vl_tl_diff[account1])
        InR_va=self.InvRva(self.va[account1])
        Larea=self.area(self.va[account1],self.nak[account1])
        p1=self.fp_mul(Nlog,InR_va)
        mp=self.fp_add(p1,Larea)
        rscore=self.fp_mul(mp,self.klsimi[account1])
        self.set_key_value(account1,rscore)
        return mp,rscore,p1,Larea