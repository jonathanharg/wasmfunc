from wasmfunc import array, i32, wasmfunc


@wasmfunc()
def fannkuch(n: i32) -> i32:
    maxFlipsCount: i32 = 0
    permSign: i32 = True
    checksum: i32 = 0

    perm1: array[i32] = list(range(n))
    count: array[i32] = list(range(n))

    temp: i32 = 0
    i: i32 = 0

    nm = n - 1
    while 1:
        k = perm1[0]
        if k:
            # perm = perm1[:]
            perm: array[i32] = list(range(n))
            i = 0
            while i < len(perm):
                perm[i] = perm1[i]
                i += 1

            flipsCount = 1
            kk = perm[k]
            while kk:
                # reverse the first k items in a list
                # perm[:k+1] = perm[k::-1]
                i = 0
                while i < ((k + 1) / 2):
                    temp = perm[i]
                    perm[i] = perm[k - i]
                    perm[k - i] = temp
                    i += 1

                flipsCount += 1
                k = kk
                kk = perm[kk]
            if maxFlipsCount < flipsCount:
                maxFlipsCount = flipsCount
            checksum += flipsCount if permSign else -flipsCount

        # Use incremental change to generate another permutation
        if permSign:
            temp = perm1[0]
            perm1[0] = perm1[1]
            perm1[1] = temp
            permSign = False
        else:
            temp = perm1[1]
            perm1[1] = perm1[2]
            perm1[2] = temp
            permSign = True

            r: i32 = 2
            while r < n - 1:
                if count[r]:
                    break
                count[r] = r
                perm0: i32 = perm1[0]
                # perm1[:r+1] = perm1[1:r+2]
                # perm1[r+1] = perm0
                i = 0
                while i <= r:
                    perm1[i] = perm1[i + 1]
                    i += 1
                perm1[r + 1] = perm0

                r += 1
            else:
                r = nm
                if not count[r]:
                    # print( checksum )
                    # return maxFlipsCount
                    # return checksum
                    count[r] = count[r] + 1
                    break
                break
            count[r] = count[r] - 1
    return checksum


testinputs_fannkuch = [(3,), (4,), (5,), (6,), (7,), (8,)]
